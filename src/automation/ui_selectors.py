# UI selectors for Practice Fusion patient summary sections
# Organized by section name for generic handler use

UI_SELECTORS = {
    "family_history": {
        "section_container": "[data-element='family-health-history-card']",
        "add_button": "[data-element='add-family-history-button']",
        "edit_button": "[data-element='family-health-history-card-list-item-button']",
        "textarea": "[data-element='family-health-history-text-area']",
        "save_button": "[data-element='btn-save']"
    },
    "social_history": {
        "section_container": "[data-element='socialHistory-section']",
        "add_button": "[data-element='past-medical-history-field-add-button']",
        "edit_button": "[data-element='past-medical-history-field-item-0']",
        "textarea": "[data-element='socialHistory-detail-text-area']",
        "save_button": "[data-element='btn-save']"
    },
    "ongoing_medical_problems": {
        "section_container": "[data-element='ongoingMedicalProblems-section']",
        "add_button": "[data-element='past-medical-history-field-add-button']",
        "edit_button": "[data-element='past-medical-history-field-item-0']",
        "textarea": "[data-element='ongoingMedicalProblems-detail-text-area']",
        "save_button": "[data-element='btn-save']"
    },
    "major_events": {
        "section_container": "[data-element='events-section']",
        "add_button": "[data-element='past-medical-history-field-add-button']",
        "edit_button": "[data-element='past-medical-history-field-item-0']",
        "textarea": "[data-element='events-detail-text-area']",
        "save_button": "[data-element='btn-save']"
    },
    "nutrition_history": {
        "section_container": "[data-element='nutritionHistory-section']",
        "add_button": "[data-element='past-medical-history-field-add-button']",
        "edit_button": "[data-element='past-medical-history-field-item-0']",
        "textarea": "[data-element='nutritionHistory-detail-text-area']",
        "save_button": "[data-element='btn-save']"
    }
}
