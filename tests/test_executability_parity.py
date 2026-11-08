from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from tests.test_executability import governed_chain, valid_chain
from tools.executability import (
    validate_admissibility_record,
    validate_assignment_artifact,
    validate_capability_evidence_artifact,
    validate_capability_profile,
    validate_execution_route,
)

ROOT = Path(__file__).resolve().parents[1]


def cross_surface_fixture():
    assignment,record,profile=deepcopy(valid_chain()); _,route=governed_chain(assignment,record,profile)
    profiles={}; evidence={}
    for segment,suffix in zip(route['segments'],['D','X','C']):
        candidate=deepcopy(profile); candidate['artifact_id']=f'CAP-{suffix}'; candidate['destination_id']=f'agent-{suffix}'; candidate['runtime_identity']=f'runtime-{suffix}'
        artifact=candidate['evidence_artifacts'][0]; artifact['artifact_id']=f'EVIDENCE-{suffix}'; artifact['runtime_identity']=candidate['runtime_identity']
        candidate['related_artifacts']=[artifact['artifact_id']]
        for claim in candidate['capability_evidence']: claim['evidence_ref']=artifact['artifact_id']
        segment['destination_id']=candidate['destination_id']; segment['runtime_identity']=candidate['runtime_identity']; segment['capability_profile_ref']=candidate['artifact_id']
        profiles[candidate['artifact_id']]=candidate; evidence[artifact['artifact_id']]=artifact
    route['final_result']['destination_id']='agent-C'
    for edge in route['handoffs']:
        edge.update(same_surface=False,internal_required_capabilities=[],source_required_capabilities=['durable_artifact_write'],target_required_capabilities=['repository_remote_read'])
    return route,profiles,evidence.get


def schema_accepts(value: object, schema: dict) -> bool:
    """Execute only the JSON-Schema keywords used by the committed parity fixtures."""
    def valid(instance: object, rule: dict) -> bool:
        if "anyOf" in rule and not any(valid(instance, option) for option in rule["anyOf"]): return False
        kind = rule.get("type")
        kinds = kind if isinstance(kind, list) else [kind] if kind else []
        if kinds:
            checks = {"object": lambda x:isinstance(x,dict), "array":lambda x:isinstance(x,list), "string":lambda x:isinstance(x,str), "null":lambda x:x is None, "boolean":lambda x:isinstance(x,bool)}
            if not any(name in checks and checks[name](instance) for name in kinds): return False
        if "const" in rule and instance != rule["const"]: return False
        if "enum" in rule and instance not in rule["enum"]: return False
        if isinstance(instance,str):
            if len(instance) < rule.get("minLength",0): return False
            if "pattern" in rule and re.fullmatch(rule["pattern"],instance) is None: return False
        if isinstance(instance,list):
            if len(instance) < rule.get("minItems",0) or len(instance) > rule.get("maxItems",10**9): return False
            if rule.get("uniqueItems") and len({json.dumps(x,sort_keys=True) for x in instance}) != len(instance): return False
            if "items" in rule and not all(valid(x,rule["items"]) for x in instance): return False
            for condition in rule.get("allOf",[]):
                matches=sum(valid(x,condition["contains"]) for x in instance)
                if matches < condition.get("minContains",1) or matches > condition.get("maxContains",10**9): return False
        if isinstance(instance,dict):
            if any(name not in instance for name in rule.get("required",[])): return False
            props=rule.get("properties",{})
            if rule.get("additionalProperties") is False and any(name not in props for name in instance): return False
            if any(name in instance and not valid(instance[name],child) for name,child in props.items()): return False
            for condition in rule.get("allOf",[]):
                if "if" in condition and valid(instance,condition["if"]) and not valid(instance,condition.get("then",{})): return False
        return True
    return valid(value,schema)


class ExecutabilitySchemaReferenceParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile_schema=json.loads((ROOT/'schemas/capability-profile.schema.json').read_text())
        cls.route_schema=json.loads((ROOT/'schemas/execution-route.schema.json').read_text())
        cls.record_schema=json.loads((ROOT/'schemas/assignment-admissibility.schema.json').read_text())
        cls.assignment_schema=json.loads((ROOT/'schemas/assignment.schema.json').read_text())
        cls.evidence_schema=cls.profile_schema['properties']['evidence_artifacts']['items']

    def test_capability_evidence_fixture_matrix_parity(self) -> None:
        _,_,profile=deepcopy(valid_chain()); base=profile['evidence_artifacts'][0]
        mutations=[
            lambda x:x.update(capabilities=[]), lambda x:x.update(capabilities=['shell','shell']),
            lambda x:x.update(capabilities=['']), lambda x:x.update(assignment_id=7),
            lambda x:x.update(input_state_ref={}), lambda x:x.pop('provenance'),
            lambda x:x.update(provenance=[]), lambda x:x.pop('observation_method'),
            lambda x:x.pop('created_from'), lambda x:x.update(observed_at='not-a-timestamp'),
        ]
        self.assertTrue(schema_accepts(base,self.evidence_schema)); self.assertEqual(validate_capability_evidence_artifact(base),[])
        for mutate in mutations:
            artifact=deepcopy(base); mutate(artifact)
            with self.subTest(artifact=artifact):
                self.assertFalse(schema_accepts(artifact,self.evidence_schema))
                self.assertTrue(validate_capability_evidence_artifact(artifact))

    def test_timestamp_strict_subset_schema_reference_parity(self) -> None:
        _,_,profile=deepcopy(valid_chain()); base=profile['evidence_artifacts'][0]
        valid=['2026-01-01T00:00:00Z','2026-01-01T00:00:00+05:30','2026-01-01T00:00:00-05:00']
        invalid=['2026-01-01T00:00:00','2026-01-01T00:00:00+14:99','2026-01-01T00:00:00+24:00','2026-01-01T00:00:00+99:99','2026-01-01T00:60:00Z','2026-01-01T00:00:60Z','2026-01-01T00:00:00.Z','not-a-timestamp']
        for timestamp in valid:
            artifact=deepcopy(base); artifact['observed_at']=timestamp
            with self.subTest(valid=timestamp): self.assertTrue(schema_accepts(artifact,self.evidence_schema)); self.assertEqual(validate_capability_evidence_artifact(artifact),[])
        for timestamp in invalid:
            artifact=deepcopy(base); artifact['observed_at']=timestamp
            with self.subTest(invalid=timestamp): self.assertFalse(schema_accepts(artifact,self.evidence_schema)); self.assertTrue(any('observed_at' in error for error in validate_capability_evidence_artifact(artifact)))
        overflow=deepcopy(base); overflow['observed_at']='9999-12-31T23:59:59-23:59'
        self.assertTrue(schema_accepts(overflow,self.evidence_schema))  # Runtime-domain normalization is reference-only.
        self.assertTrue(any('observed_at' in error for error in validate_capability_evidence_artifact(overflow)))

    def test_primary_artifact_happy_path_schema_reference_parity(self) -> None:
        assignment,record,profile=deepcopy(valid_chain()); resolver,route=governed_chain(assignment,record,profile)
        pairs=[(profile,self.profile_schema,validate_capability_profile(profile,resolver)),(record,self.record_schema,validate_admissibility_record(record)),(route,self.route_schema,validate_execution_route(route,{'CAP-1':profile},resolver)),(assignment,self.assignment_schema,validate_assignment_artifact(assignment))]
        for artifact,schema,errors in pairs:
            with self.subTest(type=artifact['artifact_type']): self.assertTrue(schema_accepts(artifact,schema)); self.assertEqual(errors,[])

    def test_route_structural_fixture_matrix_parity(self) -> None:
        assignment,record,profile=deepcopy(valid_chain()); resolver,base=governed_chain(assignment,record,profile); profiles={'CAP-1':profile}
        cases=[]
        missing=deepcopy(base); missing['segments']=missing['segments'][1:]; cases.append(missing)
        duplicate_role=deepcopy(base); duplicate_role['segments'][0]['route_role']='EXECUTION_VERIFICATION'; cases.append(duplicate_role)
        duplicate_id=deepcopy(base); duplicate_id['segments'][1]['segment_id']='delivery'; cases.append(duplicate_id)
        malformed=deepcopy(base); malformed['handoffs'][0].pop('same_surface'); cases.append(malformed)
        for route in cases:
            with self.subTest(route=route):
                reference_rejects=bool(validate_execution_route(route,profiles,resolver))
                schema_rejects=not schema_accepts(route,self.route_schema)
                if route is duplicate_id:
                    self.assertTrue(reference_rejects)  # JSON Schema cannot express key-projected uniqueness.
                else:
                    self.assertTrue(schema_rejects); self.assertTrue(reference_rejects)
        wrong_order=deepcopy(base); wrong_order['handoffs'][0]['to_segment']='durable'
        self.assertTrue(schema_accepts(wrong_order,self.route_schema))
        self.assertTrue(validate_execution_route(wrong_order,profiles,resolver))  # Deliberately semantic/reference-only.

    def test_same_surface_boolean_structural_parity(self) -> None:
        route,profiles,resolver=cross_surface_fixture()
        self.assertTrue(schema_accepts(route,self.route_schema)); self.assertEqual(validate_execution_route(route,profiles,resolver),[])
        for value in ['MISSING','false',0,None,{}]:
            invalid=deepcopy(route)
            if value == 'MISSING': invalid['handoffs'][0].pop('same_surface')
            else: invalid['handoffs'][0]['same_surface']=value
            errors=validate_execution_route(invalid,profiles,resolver)
            with self.subTest(value=value):
                self.assertFalse(schema_accepts(invalid,self.route_schema))
                expected='same_surface is required' if value == 'MISSING' else 'same_surface must be a boolean'
                self.assertTrue(any(expected in error for error in errors),errors)
        _,_,profile=deepcopy(valid_chain()); same_resolver,same_route=governed_chain(*deepcopy(valid_chain()))
        self.assertTrue(schema_accepts(same_route,self.route_schema)); self.assertEqual(validate_execution_route(same_route,{'CAP-1':profile},same_resolver),[])

    def test_same_actor_continuation_requires_an_explicit_same_surface_declaration(self) -> None:
        _,_,profile=deepcopy(valid_chain()); resolver,route=governed_chain(*deepcopy(valid_chain()))
        profiles={'CAP-1':profile}
        for edge in route['handoffs']:
            edge['same_actor_continuation']=True
            edge['internal_required_capabilities']=[]
        self.assertTrue(schema_accepts(route,self.route_schema))
        self.assertEqual(validate_execution_route(route,profiles,resolver),[])
        for mode in ('omitted',False,1,'true'):
            invalid=deepcopy(route)
            if mode == 'omitted': invalid['handoffs'][0].pop('same_actor_continuation')
            else: invalid['handoffs'][0]['same_actor_continuation']=mode
            with self.subTest(mode=mode):
                self.assertFalse(schema_accepts(invalid,self.route_schema))
                self.assertTrue(validate_execution_route(invalid,profiles,resolver))
        cross,cross_profiles,cross_resolver=cross_surface_fixture()
        cross['handoffs'][0]['same_actor_continuation']=True
        self.assertFalse(schema_accepts(cross,self.route_schema))
        self.assertTrue(any('requires the same surface' in error for error in validate_execution_route(cross,cross_profiles,cross_resolver)))
        different=deepcopy(route); different['segments'][1]['runtime_identity']='another-runtime'
        self.assertTrue(any('false same-surface equivalence' in error for error in validate_execution_route(different,profiles,resolver)))
        still_required=deepcopy(route); still_required['handoffs'][0]['internal_required_capabilities']=['not-proven']
        self.assertTrue(any('unproven internal capabilities' in error for error in validate_execution_route(still_required,profiles,resolver)))

    def test_assignment_route_binding_is_deliberately_semantic(self) -> None:
        assignment,record,profile=deepcopy(valid_chain())
        missing=deepcopy(assignment); missing['execution_contract'].pop('route_ref')
        self.assertFalse(schema_accepts(missing,self.assignment_schema)); self.assertTrue(validate_assignment_artifact(missing))
        # Cross-artifact identity and endpoint equality cannot be expressed by these standalone schemas.
        self.assertTrue(schema_accepts(assignment,self.assignment_schema))


if __name__ == '__main__': unittest.main()
