use kix_feature_ir::*;
use kix_types::KixId;
use serde_json::Value;
use std::{collections::BTreeMap, process::Command, sync::OnceLock};

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum V {
    Null,
    Bool(bool),
    I(i64),
    U(u64),
    B(Vec<u8>),
    F(String),
}
impl V {
    pub fn bytes(text: &str) -> Self {
        Self::B(text.as_bytes().to_vec())
    }
    pub fn is_null(&self) -> bool {
        *self == Self::Null
    }
}
pub type Rows = Vec<Vec<V>>;
pub type Outcome = Result<Rows, String>;
#[derive(Clone, Debug)]
pub struct Table {
    pub schema: DatasetSchema,
    pub rows: Rows,
}
#[derive(Clone, Debug)]
pub struct Data {
    pub tables: Vec<Table>,
    pub trace: Value,
    pub fixture_kind: String,
    pub names: BTreeMap<(String, String), ColumnId>,
}
pub fn id(n: u8) -> KixId {
    KixId::from_bytes([n; 16])
}
pub fn dataset(n: u8) -> DatasetRef {
    DatasetRef {
        dataset_id: id(n),
        schema_version: 1,
    }
}
pub fn schema(n: u8, columns: &[(u16, OutputKind)]) -> DatasetSchema {
    DatasetSchema {
        dataset: dataset(n),
        columns: columns
            .iter()
            .map(|(c, kind)| ColumnSchema {
                column: ColumnId(*c),
                kind: *kind,
            })
            .collect(),
    }
}
impl Data {
    pub fn synthetic(tables: Vec<Table>) -> Self {
        Self {
            tables,
            trace: serde_json::json!({"derivation": "synthetic boundary dataset, not source rows"}),
            fixture_kind: "synthetic-boundary-characterization".into(),
            names: BTreeMap::new(),
        }
    }
    pub fn catalog(&self) -> Vec<DatasetSchema> {
        self.tables.iter().map(|t| t.schema.clone()).collect()
    }
    pub fn table(&self, ds: DatasetRef) -> &Table {
        self.tables.iter().find(|t| t.schema.dataset == ds).unwrap()
    }
    pub fn column(&self, table: &str, column: &str) -> ColumnId {
        self.names[&(table.into(), column.into())]
    }
}
pub fn index(schema: &[ColumnSchema], c: ColumnId) -> usize {
    schema.iter().position(|s| s.column == c).unwrap()
}
pub fn name(c: ColumnId) -> String {
    format!("c{}", c.0)
}
pub fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}
fn unhex(text: &str) -> Vec<u8> {
    (0..text.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap())
        .collect()
}
pub fn money(text: &str) -> Result<u128, String> {
    let parsed = text
        .parse::<u128>()
        .map_err(|_| "invalid u128".to_string())?;
    if parsed.to_string() != text {
        return Err("noncanonical u128".into());
    }
    Ok(parsed)
}
pub fn exported() -> &'static Data {
    static DATA: OnceLock<Data> = OnceLock::new();
    DATA.get_or_init(|| {
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../..");
        let source = std::env::var("KIX_AUDIT_SOURCE").unwrap_or("synthetic".into());
        let output = Command::new("python3")
            .current_dir(root)
            .args(["-m", "analytics_audit.prepare_export", "--source", &source])
            .output()
            .expect("python export admission");
        assert!(
            output.status.success(),
            "admission failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        let bundle: Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(bundle["mapping"]["version"], "kix-local-export-types/1");
        let mut data = Data {
            tables: vec![],
            trace: bundle["exportTrace"].clone(),
            fixture_kind: bundle["source"]["fixtureKind"].as_str().unwrap().into(),
            names: BTreeMap::new(),
        };
        let mapping = &bundle["mapping"];
        for (table_index, (table, description)) in
            mapping["tables"].as_object().unwrap().iter().enumerate()
        {
            let mut columns = vec![];
            let specs = description["columns"].as_object().unwrap();
            for (i, (column, kind)) in specs.iter().enumerate() {
                let column_id = ColumnId((table_index * 100 + i + 1) as u16);
                let kind = match kind.as_str().unwrap() {
                    "int" => OutputKind::U64,
                    "epoch-ms-int" => OutputKind::I64,
                    "bool" => OutputKind::Bool,
                    s if s.starts_with("vocab:") => OutputKind::Category,
                    _ => OutputKind::Bytes,
                };
                columns.push(ColumnSchema {
                    column: column_id,
                    kind,
                });
                data.names
                    .insert((table.clone(), column.clone()), column_id);
            }
            let rows = bundle["tables"][table]
                .as_array()
                .unwrap()
                .iter()
                .map(|row| {
                    specs
                        .iter()
                        .map(|(column, kind)| {
                            let value = &row[column];
                            match kind.as_str().unwrap() {
                                "int" => V::U(value.as_u64().unwrap()),
                                "epoch-ms-int" => V::I(value.as_i64().unwrap()),
                                "bool" => V::Bool(value.as_bool().unwrap()),
                                "binary(32)-hex" | "binary(16)-hex" | "blob-hex" => {
                                    V::B(unhex(value.as_str().unwrap()))
                                }
                                "u128-decimal-text" => {
                                    let text = value.as_str().unwrap();
                                    money(text).unwrap();
                                    V::bytes(text)
                                }
                                s if s.starts_with("vocab:") => {
                                    let vocab = &s[6..];
                                    // Logical vocabulary name + decoded semantic value, never dictionary index.
                                    assert!(
                                        mapping["vocabularies"][vocab]
                                            .as_array()
                                            .unwrap()
                                            .contains(value)
                                    );
                                    V::bytes(&format!("{vocab}/1:{}", value.as_str().unwrap()))
                                }
                                _ => V::bytes(value.as_str().unwrap()),
                            }
                        })
                        .collect()
                })
                .collect();
            data.tables.push(Table {
                schema: DatasetSchema {
                    dataset: dataset((table_index + 1) as u8),
                    columns,
                },
                rows,
            });
        }
        data.trace["auditSource"] = bundle["source"].clone();
        data
    })
}
