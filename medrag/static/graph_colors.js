const nodeColors = new Map([
    ['disease', '#67e8f9'],
    ['syndrome', '#a7f3d0'],
    ['symptom', '#fed7aa'],
    ['sign', '#fde68a'],
    ['finding', '#c4b5fd'],
    ['procedure', '#e9d5ff'],
    ['drug', '#f9a8d4'],
    ['drug_class', '#fbcfe8'],
    ['lab_test', '#7dd3fc'],
    ['imaging_test', '#5eead4'],
    ['treatment', '#86efac'],
    ['mechanism', '#c7d2fe'],
    ['physiologic_process', '#bef264'],
    ['complication', '#fca5a5'],
    ['risk_factor', '#fdba74'],
    ['outcome', '#fda4af'],
]);

const nodeTypeAliases = new Map([
    ['condition', 'disease'],
    ['clinical_condition', 'disease'],
    ['clinical_syndrome', 'syndrome'],
    ['medication', 'drug'],
    ['medication_class', 'drug_class'],
    ['test', 'lab_test'],
    ['diagnostic_test', 'lab_test'],
    ['management_strategy', 'treatment'],
    ['immunization', 'treatment'],
]);

export function nodeTypeColor(type) {
    return nodeColors.get(nodeTypeAliases.get(type) ?? type) ?? '#bfdbfe';
}

// Match whole words in the stored relationship names. Safety qualifiers take
// precedence over the actions they qualify.
const relationshipColors = [
    [/(?:^|_)(?:contraindicat[a-z]*|avoid|warning|safety|adverse_effects?|not_recommended|do_not_miss|urgent)(?:_|$)/, 'rgba(251, 113, 133, 0.85)'],
    [/(?:^|_)(?:caus[a-z]*|risk|complicat[a-z]*|predisposes|precipitates)(?:_|$)/, 'rgba(251, 146, 60, 0.85)'],
    [/(?:^|_)(?:diagnos[a-z]*|evaluat[a-z]*|assess[a-z]*|screen[a-z]*|test[a-z]*|differential|differentiat[a-z]*|monitor[a-z]*|suggested_by)(?:_|$)/, 'rgba(125, 211, 252, 0.85)'],
    [/(?:^|_)(?:treat[a-z]*|manag[a-z]*|therap[a-z]*|first_line|drug_option|recommended_for|prevent[a-z]*)(?:_|$)/, 'rgba(134, 239, 172, 0.85)'],
    [/(?:^|_)(?:present[a-z]*|clinical_feature|has_finding|sign|symptom)(?:_|$)/, 'rgba(253, 224, 138, 0.85)'],
    [/(?:^|_)(?:subtype|classif[a-z]*|defined|component|part_of|includes)(?:_|$)/, 'rgba(196, 181, 253, 0.85)'],
];

export function relationshipTypeColor(type = '') {
    return relationshipColors.find(([pattern]) => pattern.test(type))?.[1] ?? 'rgba(255, 255, 255, 0.32)';
}
