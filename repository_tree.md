# Repository Tree Structure

```text
urban-exploration-platform/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE/
│   └── workflows/
├── assets/
│   ├── fonts/
│   ├── icons/
│   ├── images/
│   └── sounds/
├── backend/
│   ├── app/
│   │   ├── api_v1/
│   │   │   └── endpoints/
│   │   ├── core/
│   │   │   ├── config/
│   │   │   │   └── settings.py
│   │   │   ├── database.py
│   │   │   └── security/
│   │   │       └── jwt.py
│   │   ├── events/
│   │   │   ├── event_bus.py
│   │   │   └── tasks.py
│   │   ├── main.py
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── exploration/
│   │   │   ├── game_engine/
│   │   │   ├── missions/
│   │   │   ├── routes/
│   │   │   └── users/
│   │   └── shared/
│   │       └── utils/
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── migrations/
│   │   └── versions/
│   ├── pytest.ini
│   ├── requirements.txt
│   └── tests/
│       ├── e2e/
│       ├── integration/
│       └── unit/
├── configs/
│   ├── nginx/
│   ├── redis/
│   └── valhalla/
├── docs/
│   ├── adr/
│   ├── api/
│   └── architecture/
├── infrastructure/
│   ├── docker/
│   │   └── docker-compose.yml
│   ├── kubernetes/
│   │   ├── base/
│   │   │   └── kustomization.yaml
│   │   └── overlays/
│   │       ├── dev/
│   │       └── prod/
│   └── terraform/
│       ├── environments/
│       │   ├── dev/
│       │   ├── prod/
│       │   └── staging/
│       ├── main.tf
│       ├── modules/
│       │   ├── eks/
│       │   ├── rds/
│       │   └── vpc/
│       ├── outputs.tf
│       └── variables.tf
├── mobile/
│   ├── analysis_options.yaml
│   ├── android/
│   ├── ios/
│   ├── lib/
│   │   ├── app.dart
│   │   ├── core/
│   │   │   ├── network/
│   │   │   ├── theme/
│   │   │   └── utils/
│   │   ├── features/
│   │   │   ├── exploration/
│   │   │   ├── map/
│   │   │   │   ├── data/
│   │   │   │   │   └── repositories/
│   │   │   │   ├── domain/
│   │   │   │   │   └── usecases/
│   │   │   │   └── presentation/
│   │   │   │       ├── bloc/
│   │   │   │       └── widgets/
│   │   │   ├── missions/
│   │   │   └── profile/
│   │   ├── main.dart
│   │   ├── services/
│   │   └── shared/
│   │       └── widgets/
│   ├── pubspec.yaml
│   └── test/
│       ├── unit/
│       └── widget/
├── scripts/
│   ├── db/
│   └── deploy/
├── tools/
│   └── generators/
├── .gitignore
├── LICENSE
├── README.md
└── setup_project.ps1