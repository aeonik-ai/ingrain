use std::path::PathBuf;
use std::process::ExitCode;
use std::str::FromStr;

use clap::{Parser, Subcommand};
use ingrain_core::{
    hydrate, read_report, verify_store, HydrateLevel, HydrateOptions, IngrainStore, StoreReport,
};

#[derive(Debug, Parser)]
#[command(
    name = "ingrain-rs",
    about = "Read-only Rust inspector for Aeonik Ingrain stores"
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Debug, Subcommand)]
enum Commands {
    /// Hydrate compact learned-experience context from an existing store.
    Hydrate {
        #[arg(long, default_value = ".ingrain")]
        home: PathBuf,
        #[arg(long, default_value = "")]
        query: String,
        #[arg(long, default_value_t = 12)]
        limit: usize,
        #[arg(long = "max-chars", default_value_t = 6000)]
        max_chars: usize,
        #[arg(long, default_value = "cards")]
        level: HydrateLevelArg,
    },
    /// Report counts and latest rows for an existing store.
    Report {
        #[arg(long, default_value = ".ingrain")]
        home: PathBuf,
        #[arg(long)]
        json: bool,
    },
    /// Verify whether an Ingrain store is present and readable.
    VerifyStore {
        #[arg(long, default_value = ".ingrain")]
        home: PathBuf,
        #[arg(long)]
        json: bool,
    },
}

#[derive(Debug, Clone, Copy)]
enum HydrateLevelArg {
    Brief,
    Cards,
    Evidence,
}

impl FromStr for HydrateLevelArg {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "brief" => Ok(Self::Brief),
            "cards" => Ok(Self::Cards),
            "evidence" => Ok(Self::Evidence),
            other => Err(format!(
                "invalid hydration level {other:?}; use brief, cards, or evidence"
            )),
        }
    }
}

impl From<HydrateLevelArg> for HydrateLevel {
    fn from(level: HydrateLevelArg) -> Self {
        match level {
            HydrateLevelArg::Brief => Self::Brief,
            HydrateLevelArg::Cards => Self::Cards,
            HydrateLevelArg::Evidence => Self::Evidence,
        }
    }
}

fn main() -> ExitCode {
    match run(Cli::parse()) {
        Ok(code) => code,
        Err(error) => {
            eprintln!("ingrain-rs: {error}");
            ExitCode::from(2)
        }
    }
}

fn run(cli: Cli) -> Result<ExitCode, Box<dyn std::error::Error>> {
    match cli.command {
        Commands::Hydrate {
            home,
            query,
            limit,
            max_chars,
            level,
        } => {
            let output = hydrate(
                &IngrainStore::new(home),
                &HydrateOptions {
                    query,
                    limit,
                    max_chars,
                    level: level.into(),
                },
            )?;
            if !output.is_empty() {
                println!("{output}");
            }
            Ok(ExitCode::SUCCESS)
        }
        Commands::Report { home, json } => {
            let store = IngrainStore::new(home);
            match read_report(&store) {
                Ok(report) => {
                    print_report(&report, json)?;
                    Ok(ExitCode::SUCCESS)
                }
                Err(error) => {
                    if json {
                        let report = verify_store(&store);
                        print_report(&report, true)?;
                    }
                    eprintln!("ingrain-rs: {error}");
                    Ok(ExitCode::from(2))
                }
            }
        }
        Commands::VerifyStore { home, json } => {
            let report = verify_store(&IngrainStore::new(home));
            print_report(&report, json)?;
            if report.db_readable {
                Ok(ExitCode::SUCCESS)
            } else {
                Ok(ExitCode::from(2))
            }
        }
    }
}

fn print_report(report: &StoreReport, json: bool) -> Result<(), Box<dyn std::error::Error>> {
    if json {
        println!("{}", serde_json::to_string_pretty(report)?);
    } else {
        println!("Ingrain store: {}", report.home);
        println!("database: {}", report.db_path);
        println!(
            "status: {}",
            if report.db_readable {
                "readable"
            } else {
                "unreadable"
            }
        );
        println!("ledger_events: {}", report.counts.ledger_events);
        println!("promotions: {}", report.counts.promotions);
        println!("compiled_pages: {}", report.counts.compiled_pages);
        if let Some(ratio) = report.event_to_promotion_ratio {
            println!("event_to_promotion_ratio: {ratio:.3}");
        }
        if let Some(error) = &report.error {
            println!("error: {error}");
        }
    }
    Ok(())
}
