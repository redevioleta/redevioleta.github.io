// Rede Violeta — Azure Container Apps + Azure Database for PostgreSQL Flexible Server.
// Deploy em duas etapas (ver backend/AZURE_DEPLOY.md): deployApp=false, publicar imagem no ACR, deployApp=true.
targetScope = 'resourceGroup'

@description('Prefixo curto para nomear recursos (3-12 caracteres minúsculos/números).')
@minLength(3)
@maxLength(12)
param namePrefix string = 'redevioleta'

param location string = resourceGroup().location

@description('Se false, cria apenas infraestrutura base (ACR, banco, ambiente). Se true, cria também o Container App.')
param deployApp bool = false

@description('Tag da imagem no ACR (repositório rede-violeta-api).')
param imageTag string = 'latest'

@description('Origens CORS permitidas, separadas por vírgula.')
param corsOrigins string = 'https://redevioleta.github.io'

@description('Login do administrador do PostgreSQL.')
param postgresAdminLogin string = 'rvadmin'

@secure()
@description('Senha do administrador do PostgreSQL. Passe via CLI/Key Vault; nunca versione.')
param postgresAdminPassword string

@secure()
@description('Chave da API Gemini (opcional; vazio desativa a IA externa).')
param geminiApiKey string = ''

param geminiModel string = 'gemini-2.5-flash'

@description('Mantenha 1: o seed inicial roda na inicialização do contêiner.')
@minValue(1)
param maxReplicas int = 1

var suffix = uniqueString(resourceGroup().id)
var acrName = toLower('${namePrefix}${suffix}')
var pgName = toLower('${namePrefix}-pg-${suffix}')
var dbName = 'redevioleta'
var imageName = '${acr.properties.loginServer}/rede-violeta-api:${imageTag}'
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-logs-${suffix}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
  }
}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-id-${suffix}'
  location: location
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, identity.id, acrPullRoleId)
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: pgName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: { storageSizeGB: 32 }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: { mode: 'Disabled' }
    network: { publicNetworkAccess: 'Enabled' }
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: postgres
  name: dbName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Permite apenas serviços do Azure (0.0.0.0) — inclui o Container Apps. Para isolamento total,
// migre para VNet integration/Private Endpoint (ver guia).
resource allowAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-12-01-preview' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-env-${suffix}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

var databaseUrl = 'postgresql+psycopg://${postgresAdminLogin}:${uriComponent(postgresAdminPassword)}@${postgres.properties.fullyQualifiedDomainName}:5432/${dbName}?sslmode=require'

resource app 'Microsoft.App/containerApps@2024-03-01' = if (deployApp) {
  name: '${namePrefix}-api'
  location: location
  dependsOn: [ acrPull, database, allowAzure ]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: identity.id
        }
      ]
      secrets: concat([
        {
          name: 'database-url'
          value: databaseUrl
        }
      ], empty(geminiApiKey) ? [] : [
        {
          name: 'gemini-api-key'
          value: geminiApiKey
        }
      ])
    }
    template: {
      containers: [
        {
          name: 'api'
          image: imageName
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: concat([
            { name: 'PORT', value: '8000' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'CORS_ORIGINS', value: corsOrigins }
            { name: 'GEMINI_MODEL', value: geminiModel }
          ], empty(geminiApiKey) ? [] : [
            { name: 'GEMINI_API_KEY', secretRef: 'gemini-api-key' }
          ])
          probes: [
            {
              type: 'Startup'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 5
              periodSeconds: 5
              failureThreshold: 24
            }
            {
              type: 'Liveness'
              httpGet: { path: '/health', port: 8000 }
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: { path: '/health', port: 8000 }
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: maxReplicas
      }
    }
  }
}

output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
output postgresHost string = postgres.properties.fullyQualifiedDomainName
output apiBaseUrl string = deployApp ? 'https://${app!.properties.configuration.ingress.fqdn}/api/v1' : ''
