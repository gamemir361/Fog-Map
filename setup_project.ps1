# ==============================================================================
# Urban Exploration Game Platform - Project Bootstrap Script
# ==============================================================================

Write-Host "Bootstrapping Urban Exploration Game Platform..." -ForegroundColor Green

# 1. Define Directory Structure
$directories = @(
    ".github/workflows",
    ".github/ISSUE_TEMPLATE",
    ".github/PULL_REQUEST_TEMPLATE",
    "docs/adr",
    "docs/architecture",
    "docs/api",
    "backend/app/api_v1/endpoints",
    "backend/app/core/security",
    "backend/app/core/config",
    "backend/app/modules/auth",
    "backend/app/modules/users",
    "backend/app/modules/routes",
    "backend/app/modules/exploration",
    "backend/app/modules/missions",
    "backend/app/modules/game_engine",
    "backend/app/shared/utils",
    "backend/app/events",
    "backend/migrations/versions",
    "backend/tests/unit",
    "backend/tests/integration",
    "backend/tests/e2e",
    "mobile/android",
    "mobile/ios",
    "mobile/lib/core/theme",
    "mobile/lib/core/network",
    "mobile/lib/core/utils",
    "mobile/lib/shared/widgets",
    "mobile/lib/services",
    "mobile/lib/features/map/presentation/bloc",
    "mobile/lib/features/map/presentation/widgets",
    "mobile/lib/features/map/domain/usecases",
    "mobile/lib/features/map/data/repositories",
    "mobile/lib/features/exploration",
    "mobile/lib/features/missions",
    "mobile/lib/features/profile",
    "mobile/test/unit",
    "mobile/test/widget",
    "infrastructure/terraform/environments/dev",
    "infrastructure/terraform/environments/staging",
    "infrastructure/terraform/environments/prod",
    "infrastructure/terraform/modules/vpc",
    "infrastructure/terraform/modules/eks",
    "infrastructure/terraform/modules/rds",
    "infrastructure/kubernetes/base",
    "infrastructure/kubernetes/overlays/dev",
    "infrastructure/kubernetes/overlays/prod",
    "infrastructure/docker",
    "scripts/db",
    "scripts/deploy",
    "tools/generators",
    "configs/nginx",
    "configs/valhalla",
    "configs/redis",
    "assets/images",
    "assets/icons",
    "assets/fonts",
    "assets/sounds"
)

# 2. Create Directories
foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    # Create .gitkeep to ensure empty directories are tracked by git
    New-Item -ItemType File -Force -Path "$dir/.gitkeep" | Out-Null
}

# 3. Create Placeholder Files for Backend (Python/FastAPI)
$backendFiles = @(
    "backend/app/main.py",
    "backend/app/core/config/settings.py",
    "backend/app/core/security/jwt.py",
    "backend/app/core/database.py",
    "backend/app/events/event_bus.py",
    "backend/app/events/tasks.py",
    "backend/requirements.txt",
    "backend/Dockerfile",
    "backend/pytest.ini",
    "backend/alembic.ini"
)

foreach ($file in $backendFiles) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

# 4. Create Placeholder Files for Mobile (Flutter)
$mobileFiles = @(
    "mobile/lib/main.dart",
    "mobile/lib/app.dart",
    "mobile/pubspec.yaml",
    "mobile/analysis_options.yaml"
)

foreach ($file in $mobileFiles) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

# 5. Create Placeholder Files for Infrastructure
$infraFiles = @(
    "infrastructure/docker/docker-compose.yml",
    "infrastructure/terraform/main.tf",
    "infrastructure/terraform/variables.tf",
    "infrastructure/terraform/outputs.tf",
    "infrastructure/kubernetes/base/kustomization.yaml"
)

foreach ($file in $infraFiles) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}

# 6. Initialize Git and Commit
Write-Host "Initializing Git Repository..." -ForegroundColor Yellow
git init
git branch -M main
git add .
git commit -m "chore: initial project bootstrap structure"

Write-Host "Project Bootstrap Completed Successfully!" -ForegroundColor Green