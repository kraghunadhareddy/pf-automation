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
    },
    "preventive_care": {
        "section_container": "[data-element='preventativeCare-section']",
        "add_button": "[data-element='past-medical-history-field-add-button']",
        "edit_button": "[data-element='past-medical-history-field-item-0']",
        "textarea": "[data-element='preventativeCare-detail-text-area']",
        "save_button": "[data-element='btn-save']"
    },
    # Scheduler toolbar: Facility/Hormone Center dropdown
    "facility_select": {
        "container": ".scheduler-toolbar__select-facilities",
        "button": ".scheduler-toolbar__select-facilities [data-element='dropdown']",
        "selection_text": ".scheduler-toolbar__select-facilities .composable-select__selection",
        # Open menu candidates and options
        "listbox": "[role='listbox']",
        "options": "[role='option'], .composable-select__option"
    },
    # Scheduler tabs (agenda/appointments view)
    "schedule_tabs": {
        "appointments": "[data-element='scheduler-tab-0']"
    }
}
