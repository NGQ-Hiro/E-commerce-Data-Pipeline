## Commit Message Instructions

Keep commit messages short and concise.

Start your commit message with a **category emoji** from the list below to describe the purpose of the change.

Format: `<emoji> <category>: <message>`

Examples:
🌊 Add new daily ingestion DAG
🐘 Optimize Spark shuffle partitions
⚙️ Update production database connection

### Categories

* 🌊 **Workflow**: Changes to orchestration logic (e.g., Airflow DAGs, tasks, dependencies).
Example: `🌊 Add retries to monthly reporting DAG`
* 🧠 **Processing**: Updates to core data processing logic (e.g., Spark/Flink jobs, transformation scripts, SQL queries).
Example: `🧠 Refactor user session aggregation logic`
* 🗄️ **Schemas**: Changes to data models, DDL, or table definitions (e.g., Iceberg, SQL, Protobuf).
Example: `🗄️ Add partition column to transactions table`
* ☁️ **Infra**: Infrastructure as Code or environment changes (e.g., Docker, Terraform, Cloud configurations).
Example: `☁️ Increase memory limit for worker nodes`
* ⚙️ **Config**: Updates to configuration files, environment variables, or connection settings.
Example: `⚙️ Update max_active_runs in airflow.cfg`
* 🧪 **Quality**: Data quality checks, unit tests, or validation rules.
Example: `🧪 Add null check for user_id field`
* 📦 **Deps**: Dependency management (e.g., `requirements.txt`, JARs, library updates).
Example: `📦 Upgrade PySpark to version 3.5`
* 📊 **Data**: Updates to static datasets, seeds, or lookups.
Example: `📊 Update country code mapping CSV`
* 📜 **Docs**: Documentation for pipelines, data dictionaries, or runbooks.
Example: `📜 Update README with backfill instructions`
* 🐛 **Bug**: Fixes for pipeline failures or incorrect data outputs.
Example: `🐛 Fix timestamp parsing error in bronze layer`

---

### Tips

* **Scope it**: If a change affects multiple pipelines, mention the specific DAG or dataset in the message.
* **Be Atomic**: Separate infrastructure changes (☁️) from logic changes (🧠).