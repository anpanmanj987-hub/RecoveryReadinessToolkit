"""Synthetic inputs. Evidence records below are fixtures, not real cloud evidence."""
import copy

AS_OF = '2026-10-14'
BOOL_FIELDS = '''lock_finalized control_graph_complete network_graph_complete independent_identity dedicated_admin_device independent_approval runbook_available control_plane_exported network_default_deny egress_allowlist immutable_applies_to_points recovery_point_exists recovery_point_reviewed independent_backup_approval key_usable restore_supported restore_tested m365_data_covered m365_identity_plan m365_config_plan m365_domain_plan quarantine_separate malware_scan_recorded configuration_diff_reviewed permissions_reviewed secrets_rotated log_immutable log_capture_verified release_approval application_tested external_dependencies_tested'''.split()
TESTED_FIELDS = '''recovery_point_reviewed key_usable restore_tested malware_scan_recorded configuration_diff_reviewed permissions_reviewed secrets_rotated log_capture_verified release_approval application_tested external_dependencies_tested measured_rto_hours measured_data_loss_hours'''.split()

def base_model():
    facts = {k: {'value': True, 'evidence': ['test' if k in TESTED_FIELDS else 'cfg']} for k in BOOL_FIELDS}
    facts.update({k: {'value': v, 'evidence': ['test' if k in TESTED_FIELDS else 'cfg']} for k, v in {
        'immutable_mode': 'azure_locked', 'protection_until': '2027-01-31',
        'retention_days': 120, 'required_retention_days': 90,
        'key_management': 'customer', 'restore_method': 'vendor',
        'rto_hours': 8, 'measured_rto_hours': 4, 'rpo_hours': 24,
        'measured_data_loss_hours': 12,
    }.items()})
    return {
        'schema_version': '1.0',
        'project': {'id': 'fictional-company', 'name': '架空企業・レビュー', 'demo': True},
        'evidence': [
            {'id': 'cfg', 'type': 'configuration', 'collected_at': AS_OF, 'reference': 'SYNTHETIC configuration fixture'},
            {'id': 'test', 'type': 'tested', 'collected_at': AS_OF, 'reference': 'SYNTHETIC test fixture'},
            {'id': 'say', 'type': 'self_reported', 'collected_at': AS_OF, 'reference': 'Synthetic interview'},
        ],
        'nodes': [
            {'id': 'prod-tenant', 'label': '本番ID', 'kind': 'tenant', 'provider': 'azure', 'plane': 'production', 'evidence': ['cfg']},
            {'id': 'rec-tenant', 'label': '復旧ID', 'kind': 'tenant', 'provider': 'azure', 'plane': 'recovery', 'evidence': ['cfg']},
            {'id': 'prod-sub', 'label': '本番Sub', 'kind': 'subscription', 'provider': 'azure', 'plane': 'production', 'tenant': 'prod-tenant', 'evidence': ['cfg']},
            {'id': 'rec-sub', 'label': '復旧Sub', 'kind': 'subscription', 'provider': 'azure', 'plane': 'recovery', 'tenant': 'rec-tenant', 'evidence': ['cfg']},
            {'id': 'vault', 'label': '保管先', 'kind': 'backup', 'provider': 'azure', 'plane': 'backup', 'evidence': ['cfg']},
            {'id': 'key', 'label': '復号鍵', 'kind': 'key', 'provider': 'azure', 'plane': 'backup', 'evidence': ['cfg']},
            {'id': 'logs', 'label': '検証ログ', 'kind': 'log_store', 'provider': 'azure', 'plane': 'recovery', 'evidence': ['cfg']},
        ],
        'edges': [],
        'scenarios': [{'id': 'tenant-takeover', 'name': '本番全体管理者侵害', 'compromised': ['prod-tenant'], 'azure_global_admin_tenants': ['prod-tenant']}],
        'assessments': [{'id': 'core', 'name': '基幹業務', 'provider': 'azure', 'workload': 'azure_vm', 'production_node': 'prod-sub', 'recovery_node': 'rec-sub', 'backup_node': 'vault', 'key_node': 'key', 'log_node': 'logs', 'facts': facts}],
    }

def fact(model, key, value, evidence=None):
    model['assessments'][0]['facts'][key] = {'value': value, 'evidence': evidence if evidence is not None else ['cfg']}
    return model

def edge(model, source, target, relation='controls', evidence=None):
    model['edges'].append({'id': 'edge-' + str(len(model['edges'])), 'source': source, 'target': target, 'relation': relation, 'evidence': ['cfg'] if evidence is None else evidence})
    return model

def clone(model):
    return copy.deepcopy(model)
