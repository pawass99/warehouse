from __future__ import annotations

import calendar
import math
import random
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATABASE_DIR = ROOT_DIR / "database"
CSV_PATH = DATA_DIR / "repository_activity.csv"
DB_PATH = DATABASE_DIR / "repository_analytics.db"
TABLE_NAME = "repository_activity"


@dataclass(frozen=True)
class ProjectProfile:
    name: str
    size: str
    developer_count: int
    ideal_developer_count: int
    repositories_by_team: dict[str, list[str]]
    base_activity_per_developer: float
    complexity: float
    quality_risk: float


PROJECTS = [
    ProjectProfile(
        name="AuthFlow",
        size="Small",
        developer_count=4,
        ideal_developer_count=4,
        repositories_by_team={
            "Backend": ["authflow-api"],
            "Frontend": ["authflow-web"],
            "DevOps": ["authflow-infra"],
        },
        base_activity_per_developer=27,
        complexity=0.72,
        quality_risk=0.07,
    ),
    ProjectProfile(
        name="CampusPay",
        size="Small",
        developer_count=5,
        ideal_developer_count=5,
        repositories_by_team={
            "Backend": ["campuspay-api"],
            "Mobile": ["campuspay-mobile"],
            "Data": ["campuspay-analytics"],
        },
        base_activity_per_developer=25,
        complexity=0.78,
        quality_risk=0.08,
    ),
    ProjectProfile(
        name="InventoryHub",
        size="Medium",
        developer_count=9,
        ideal_developer_count=10,
        repositories_by_team={
            "Backend": ["inventoryhub-api"],
            "Frontend": ["inventoryhub-admin"],
            "Data": ["inventoryhub-reporting"],
            "DevOps": ["inventoryhub-infra"],
        },
        base_activity_per_developer=23,
        complexity=0.86,
        quality_risk=0.09,
    ),
    ProjectProfile(
        name="LearningPortal",
        size="Medium",
        developer_count=12,
        ideal_developer_count=11,
        repositories_by_team={
            "Backend": ["learningportal-api"],
            "Frontend": ["learningportal-web"],
            "Mobile": ["learningportal-mobile"],
            "Data": ["learningportal-recommendation"],
        },
        base_activity_per_developer=22,
        complexity=0.9,
        quality_risk=0.1,
    ),
    ProjectProfile(
        name="SupportSuite",
        size="Medium",
        developer_count=10,
        ideal_developer_count=12,
        repositories_by_team={
            "Backend": ["supportsuite-api"],
            "Frontend": ["supportsuite-console"],
            "Data": ["supportsuite-insights"],
            "DevOps": ["supportsuite-ops"],
        },
        base_activity_per_developer=19,
        complexity=0.94,
        quality_risk=0.12,
    ),
    ProjectProfile(
        name="CommerceCore",
        size="Large",
        developer_count=18,
        ideal_developer_count=18,
        repositories_by_team={
            "Backend": ["commercecore-api", "commercecore-payment"],
            "Frontend": ["commercecore-storefront"],
            "Mobile": ["commercecore-mobile"],
            "Data": ["commercecore-warehouse"],
            "DevOps": ["commercecore-platform"],
        },
        base_activity_per_developer=21,
        complexity=1.05,
        quality_risk=0.11,
    ),
    ProjectProfile(
        name="HealthTrack",
        size="Large",
        developer_count=22,
        ideal_developer_count=20,
        repositories_by_team={
            "Backend": ["healthtrack-api", "healthtrack-integration"],
            "Frontend": ["healthtrack-clinic"],
            "Mobile": ["healthtrack-mobile"],
            "Data": ["healthtrack-models"],
            "DevOps": ["healthtrack-platform"],
        },
        base_activity_per_developer=19,
        complexity=1.12,
        quality_risk=0.13,
    ),
    ProjectProfile(
        name="LogisticsOS",
        size="Large",
        developer_count=26,
        ideal_developer_count=20,
        repositories_by_team={
            "Backend": ["logisticsos-api", "logisticsos-routing"],
            "Frontend": ["logisticsos-control-tower"],
            "Mobile": ["logisticsos-driver"],
            "Data": ["logisticsos-forecasting"],
            "DevOps": ["logisticsos-infra"],
        },
        base_activity_per_developer=17,
        complexity=1.18,
        quality_risk=0.14,
    ),
    ProjectProfile(
        name="FinSight",
        size="Large",
        developer_count=20,
        ideal_developer_count=16,
        repositories_by_team={
            "Backend": ["finsight-api", "finsight-risk-engine"],
            "Frontend": ["finsight-dashboard"],
            "Data": ["finsight-pipeline"],
            "DevOps": ["finsight-platform"],
        },
        base_activity_per_developer=16,
        complexity=1.2,
        quality_risk=0.18,
    ),
]


FIRST_NAMES = [
    "Alya",
    "Andi",
    "Arif",
    "Ayu",
    "Bagas",
    "Bima",
    "Citra",
    "Dewi",
    "Dimas",
    "Eka",
    "Farah",
    "Fikri",
    "Gita",
    "Hana",
    "Ilham",
    "Joko",
    "Karina",
    "Laras",
    "Made",
    "Nadia",
    "Naufal",
    "Putri",
    "Raka",
    "Rani",
    "Rizky",
    "Salsa",
    "Tegar",
    "Vina",
]

LAST_NAMES = [
    "Adinata",
    "Anwar",
    "Basuki",
    "Firmansyah",
    "Hartono",
    "Kusuma",
    "Lestari",
    "Mahendra",
    "Nugraha",
    "Permata",
    "Pratama",
    "Ramadhan",
    "Santoso",
    "Saputra",
    "Wijaya",
    "Yuliani",
]


def bounded_int(rng: random.Random, mean: float, std_dev: float, minimum: int = 0) -> int:
    return max(minimum, int(round(rng.gauss(mean, std_dev))))


def month_starts(start_year: int = 2025, start_month: int = 1, number_of_months: int = 16) -> list[date]:
    months: list[date] = []
    year = start_year
    month = start_month

    for _ in range(number_of_months):
        months.append(date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1

    return months


def build_developer_assignments(rng: random.Random) -> dict[str, list[dict[str, str]]]:
    names = [f"{first} {last}" for first in FIRST_NAMES for last in LAST_NAMES]
    rng.shuffle(names)

    assignments: dict[str, list[dict[str, str]]] = {}
    cursor = 0

    for project in PROJECTS:
        teams = list(project.repositories_by_team.keys())
        project_developers: list[dict[str, str]] = []

        for index in range(project.developer_count):
            team = teams[index % len(teams)]
            project_developers.append(
                {
                    "developer_name": names[cursor],
                    "team_name": team,
                }
            )
            cursor += 1

        rng.shuffle(project_developers)
        assignments[project.name] = project_developers

    return assignments


def generate_repository_activity(seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    assignments = build_developer_assignments(rng)
    rows: list[dict[str, object]] = []
    size_activity_factor = {"Small": 1.08, "Medium": 1.0, "Large": 0.92}

    for month_index, month_start in enumerate(month_starts()):
        last_day = calendar.monthrange(month_start.year, month_start.month)[1]
        month_label = month_start.strftime("%Y-%m")
        seasonal_factor = 1 + (0.1 * math.sin((month_index / 12) * 2 * math.pi))
        release_factor = 1.15 if month_index % 4 == 2 else 1.0

        for project in PROJECTS:
            overstaffed_ratio = max(
                project.developer_count - project.ideal_developer_count, 0
            ) / project.ideal_developer_count
            understaffed_ratio = max(
                project.ideal_developer_count - project.developer_count, 0
            ) / project.ideal_developer_count

            coordination_penalty = 1 - min(0.34, overstaffed_ratio * 0.55)
            understaffing_penalty = 1 - min(0.3, understaffed_ratio * 0.5)
            productivity_multiplier = (
                size_activity_factor[project.size]
                * seasonal_factor
                * release_factor
                * coordination_penalty
                * understaffing_penalty
            )

            for developer in assignments[project.name]:
                active_day = rng.randint(1, last_day)
                activity_date = date(month_start.year, month_start.month, active_day)
                team_name = developer["team_name"]
                repository_name = rng.choice(project.repositories_by_team[team_name])

                individual_factor = rng.uniform(0.72, 1.28)
                if rng.random() < 0.035:
                    individual_factor *= rng.uniform(0.28, 0.55)

                expected_activity = (
                    project.base_activity_per_developer
                    * productivity_multiplier
                    * individual_factor
                )
                expected_activity = max(expected_activity, 3)

                commits = bounded_int(rng, expected_activity * 0.53, expected_activity * 0.13, 0)
                pull_requests = bounded_int(
                    rng, expected_activity * 0.23, expected_activity * 0.08, 0
                )
                issues_resolved = bounded_int(
                    rng, expected_activity * 0.24, expected_activity * 0.1, 0
                )

                conflict_probability = (
                    0.035
                    + (project.complexity * 0.025)
                    + (overstaffed_ratio * 0.18)
                    + (project.developer_count / 100)
                )
                conflict_probability = min(conflict_probability, 0.48)
                merge_conflicts = sum(
                    1 for _ in range(pull_requests) if rng.random() < conflict_probability
                )

                bug_probability = (
                    project.quality_risk
                    + (understaffed_ratio * 0.08)
                    + (project.complexity * 0.025)
                    + rng.uniform(-0.02, 0.025)
                )
                bug_probability = min(max(bug_probability, 0.03), 0.42)
                bugs_reported = sum(1 for _ in range(commits) if rng.random() < bug_probability)

                lines_added = bounded_int(
                    rng,
                    commits * rng.uniform(65, 180) * project.complexity,
                    max(commits * 18, 8),
                    0,
                )
                lines_deleted = bounded_int(
                    rng,
                    lines_added * rng.uniform(0.25, 0.62),
                    max(lines_added * 0.08, 6),
                    0,
                )

                rows.append(
                    {
                        "date": activity_date.isoformat(),
                        "month": month_label,
                        "project_name": project.name,
                        "project_size": project.size,
                        "team_name": team_name,
                        "developer_name": developer["developer_name"],
                        "developer_count": project.developer_count,
                        "repository_name": repository_name,
                        "commits": commits,
                        "pull_requests": pull_requests,
                        "merge_conflicts": merge_conflicts,
                        "issues_resolved": issues_resolved,
                        "bugs_reported": bugs_reported,
                        "lines_added": lines_added,
                        "lines_deleted": lines_deleted,
                    }
                )

    return pd.DataFrame(rows).sort_values(["date", "project_name", "team_name"]).reset_index(drop=True)


def seed_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    dataframe = generate_repository_activity()
    dataframe.to_csv(CSV_PATH, index=False)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        dataframe.to_sql(TABLE_NAME, connection, index=False, if_exists="replace")
        connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_date ON {TABLE_NAME}(date)"
        )
        connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_month ON {TABLE_NAME}(month)"
        )
        connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_project ON {TABLE_NAME}(project_name)"
        )
        connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_team ON {TABLE_NAME}(team_name)"
        )
        connection.commit()

    print(f"Seeded {len(dataframe):,} rows")
    print(f"CSV: {CSV_PATH}")
    print(f"SQLite database: {DB_PATH}")


if __name__ == "__main__":
    seed_database()
