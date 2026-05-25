# 06. Schema Compiler 詳細設計

## 1. スキーマコンパイラ実装 (`app/domain/services/schema_compiler.py`)

人間が承認した際に、Pydantic validator コードおよび OWL 定義ファイルを動的書き換えするモジュールです。

```python
import os
import re

class SchemaCompiler:
    def __init__(self):
        self.schema_file_path = os.path.join(
            os.path.dirname(__file__), 
            '../../interfaces/gateways/schemas/extraction_schema.py'
        )

    async def compile_pydantic_schema(self, new_class: dict) -> None:
        """LLM抽出検証用の Pydantic Schema ファイルを動的に書き換えます。"""
        with open(self.schema_file_path, 'r', encoding='utf-8') as f:
            schema_code = f.read()

        # Literal[] のマッチと追加
        enum_search_regex = r"type:\s*Literal\[\s*([^\]]+?)\s*\]"
        match = re.search(enum_search_regex, schema_code)
        
        if match:
            current_enums = [s.strip().strip("'").strip('"') for s in match.group(1).split(',')]
            class_name = f"ap:{new_class['name']}"
            if class_name not in current_enums:
                current_enums.append(class_name)
                new_enum_content = ",\n        ".join(f"'{e}'" for e in current_enums)
                
                schema_code = re.sub(
                    enum_search_regex,
                    f"type: Literal[\n        {new_enum_content}\n    ]",
                    schema_code
                )

        with open(self.schema_file_path, 'w', encoding='utf-8') as f:
            f.write(schema_code)

    async def compile_owl_ontology(self, new_class: dict) -> None:
        """W3C標準オントロジー定義ファイル (.ttl) に新規クラス記述を追記します。"""
        owl_path = os.path.join(os.getcwd(), 'docs/schema/ontology.ttl')
        ttl_fragment = f"""
###  http://example.org/ap/{new_class['name']}
ap:{new_class['name']} rdf:type owl:Class ;
       rdfs:subClassOf ap:DomainEntity ;
       rdfs:label "{new_class['name']}"@ja ;
       rdfs:comment "{new_class['description']}"@ja .
"""
        with open(owl_path, 'a', encoding='utf-8') as f:
            f.write(ttl_fragment)
```
