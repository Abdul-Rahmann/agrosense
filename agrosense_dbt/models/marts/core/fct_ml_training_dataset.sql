-- Complete feature set for training yield prediction models
-- Uses historical crop_yield data as your labeled training set
select
    -- Target variable
    cy.hg_ha_yield as target_yield,

    -- Features from crop yield dataset
    cy.area,
    cy.item as crop_type,
    cy.year,
    cy.average_rainfall_mm_per_year,
    cy.pesticides_tonnes,
    cy.avg_temp,

    -- Derived features
    cy.hg_ha_yield / cy.average_rainfall_mm_per_year as yield_efficiency,
    cy.pesticides_tonnes / cy.average_rainfall_mm_per_year as pesticide_intensity,

    -- Add temporal features
    mod(cy.year, 10) as year_in_decade,
    case when cy.year >= 2010 then 'modern' else 'historical' end as era

from {{ ref('int_crop_yield_features') }} cy
where cy.hg_ha_yield > 0  -- Remove anomalies