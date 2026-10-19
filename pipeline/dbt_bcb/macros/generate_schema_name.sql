{# Usa o nome do schema direto (staging, marts) em vez de public_staging #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name or target.schema }}
{%- endmacro %}
