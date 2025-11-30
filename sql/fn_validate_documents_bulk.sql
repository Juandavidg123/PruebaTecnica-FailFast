
-- Función: fn_validate_documents_bulk
-- Descripción: Valida documentos de manera masiva para una empresa
-- Retorna errores de:
--   - Documentos obligatorios faltantes
--   - Documentos con fechas de emisión futuras
--   - Documentos vencidos
--   - Documentos rechazados activos

CREATE OR REPLACE FUNCTION fn_validate_documents_bulk(
    p_company_id UUID,
    p_entity_type VARCHAR,
    p_entity_ids UUID[] DEFAULT NULL
)
RETURNS TABLE (
    entity_id UUID,
    entity_code VARCHAR,
    document_type_code VARCHAR,
    error_type VARCHAR,
    error_message TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH target_entities AS (
        SELECT
            e.id,
            e.entity_code,
            e.entity_name,
            e.entity_type
        FROM entities e
        WHERE e.company_id = p_company_id
          AND e.entity_type = p_entity_type
          AND e.is_active = true
          AND (
              p_entity_ids IS NULL
              OR e.id = ANY(p_entity_ids)
          )
    ),
    mandatory_doc_types AS (
        SELECT
            dt.id,
            dt.code,
            dt.name
        FROM document_types dt
        WHERE dt.entity_type = p_entity_type
          AND dt.is_mandatory = true
    ),

    current_documents AS (
        SELECT
            d.id,
            d.entity_id,
            d.document_type_id,
            d.validation_status,
            d.issue_date,
            d.expiration_date,
            dt.code AS document_type_code,
            dt.requires_issue_date,
            dt.requires_expiration_date
        FROM documents d
        INNER JOIN document_types dt ON d.document_type_id = dt.id
        WHERE d.company_id = p_company_id
          AND EXISTS (
              SELECT 1
              FROM target_entities te
              WHERE te.id = d.entity_id
          )
    ),

    missing_mandatory AS (
        SELECT
            te.id AS entity_id,
            te.entity_code,
            mdt.code AS document_type_code,
            'missing_mandatory'::VARCHAR AS error_type,
            ('Documento obligatorio faltante: ' || mdt.name)::TEXT AS error_message
        FROM target_entities te
        CROSS JOIN mandatory_doc_types mdt
        WHERE NOT EXISTS (
            SELECT 1
            FROM current_documents cd
            WHERE cd.entity_id = te.id
              AND cd.document_type_id = mdt.id
              AND cd.validation_status = 'A' -- Solo aprobados
        )
    ),

    future_issue_date AS (
        SELECT
            te.id AS entity_id,
            te.entity_code,
            cd.document_type_code,
            'future_issue_date'::VARCHAR AS error_type,
            (
                'Documento con fecha de emisión futura: ' ||
                TO_CHAR(cd.issue_date, 'YYYY-MM-DD')
            )::TEXT AS error_message
        FROM target_entities te
        INNER JOIN current_documents cd ON cd.entity_id = te.id
        WHERE cd.requires_issue_date = true
          AND cd.issue_date IS NOT NULL
          AND cd.issue_date > CURRENT_DATE
    ),

    expired_documents AS (
        SELECT
            te.id AS entity_id,
            te.entity_code,
            cd.document_type_code,
            'expired'::VARCHAR AS error_type,
            (
                'Documento vencido desde ' ||
                TO_CHAR(cd.expiration_date, 'YYYY-MM-DD')
            )::TEXT AS error_message
        FROM target_entities te
        INNER JOIN current_documents cd ON cd.entity_id = te.id
        WHERE cd.requires_expiration_date = true
          AND cd.expiration_date IS NOT NULL
          AND cd.expiration_date < CURRENT_DATE
          AND cd.validation_status = 'A' -- Solo los aprobados que están vencidos
    ),

    rejected_documents AS (
        SELECT
            te.id AS entity_id,
            te.entity_code,
            cd.document_type_code,
            'rejected'::VARCHAR AS error_type,
            'Documento rechazado requiere reemplazo'::TEXT AS error_message
        FROM target_entities te
        INNER JOIN current_documents cd ON cd.entity_id = te.id
        WHERE cd.validation_status = 'R'
    )

    SELECT * FROM missing_mandatory
    UNION ALL
    SELECT * FROM future_issue_date
    UNION ALL
    SELECT * FROM expired_documents
    UNION ALL
    SELECT * FROM rejected_documents
    ORDER BY entity_code, error_type, document_type_code;

END;
$$;

COMMENT ON FUNCTION fn_validate_documents_bulk(UUID, VARCHAR, UUID[]) IS