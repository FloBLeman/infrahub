#
# Generated by "infrahubctl protocols"
#

from __future__ import annotations

from typing import TYPE_CHECKING

from infrahub_sdk.protocols import (
    BuiltinIPAddress,
    BuiltinIPPrefix,
    CoreArtifactTarget,
    CoreNode,
)

if TYPE_CHECKING:
    from infrahub_sdk.node import RelatedNode, RelationshipManager
    from infrahub_sdk.protocols_base import (
        Boolean,
        Dropdown,
        DropdownOptional,
        Integer,
        IntegerOptional,
        String,
        StringOptional,
    )


class InfraEndpoint(CoreNode):
    connected_endpoint: RelatedNode


class OrganizationGeneric(CoreNode):
    name: String
    description: StringOptional
    tags: RelationshipManager
    asn: RelationshipManager


class LocationGeneric(CoreNode):
    name: String
    description: StringOptional


class InfraInterface(CoreNode):
    name: String
    description: StringOptional
    speed: Integer
    mtu: Integer
    enabled: Boolean
    status: DropdownOptional
    role: DropdownOptional
    device: RelatedNode
    tags: RelationshipManager


class InfraLagInterface(CoreNode):
    lacp: String
    minimum_links: Integer
    max_bundle: IntegerOptional
    mlag: RelatedNode


class InfraMlagInterface(CoreNode):
    mlag_id: Integer
    mlag_domain: RelatedNode


class InfraService(CoreNode):
    name: String


class InfraAutonomousSystem(CoreNode):
    name: String
    asn: Integer
    description: StringOptional
    organization: RelatedNode


class InfraBGPPeerGroup(CoreNode):
    name: String
    description: StringOptional
    import_policies: StringOptional
    export_policies: StringOptional
    local_as: RelatedNode
    remote_as: RelatedNode


class InfraBGPSession(CoreArtifactTarget):
    type: String
    description: StringOptional
    import_policies: StringOptional
    export_policies: StringOptional
    status: Dropdown
    role: Dropdown
    local_as: RelatedNode
    remote_as: RelatedNode
    local_ip: RelatedNode
    remote_ip: RelatedNode
    device: RelatedNode
    peer_group: RelatedNode
    peer_session: RelatedNode


class InfraBackBoneService(InfraService):
    circuit_id: String
    internal_circuit_id: String
    provider: RelatedNode
    site_a: RelatedNode
    site_b: RelatedNode


class InfraCircuit(CoreNode):
    circuit_id: String
    description: StringOptional
    vendor_id: StringOptional
    status: Dropdown
    role: Dropdown
    provider: RelatedNode
    endpoints: RelationshipManager
    bgp_sessions: RelationshipManager


class InfraCircuitEndpoint(InfraEndpoint):
    description: StringOptional
    site: RelatedNode
    circuit: RelatedNode


class LocationContinent(LocationGeneric):
    pass


class LocationCountry(LocationGeneric):
    pass


class InfraDevice(CoreArtifactTarget):
    name: String
    description: StringOptional
    type: String
    status: DropdownOptional
    role: DropdownOptional
    site: RelatedNode
    interfaces: RelationshipManager
    asn: RelatedNode
    tags: RelationshipManager
    primary_address: RelatedNode
    platform: RelatedNode
    mlag_domain: RelatedNode


class IpamIPAddress(BuiltinIPAddress):
    interface: RelatedNode


class IpamIPPrefix(BuiltinIPPrefix):
    pass


class InfraInterfaceL2(InfraInterface, InfraEndpoint, CoreArtifactTarget):
    l2_mode: String
    lacp_rate: String
    lacp_priority: Integer
    lag: RelatedNode
    untagged_vlan: RelatedNode
    tagged_vlan: RelationshipManager


class InfraInterfaceL3(InfraInterface, InfraEndpoint, CoreArtifactTarget):
    lacp_rate: String
    lacp_priority: Integer
    ip_addresses: RelationshipManager
    lag: RelatedNode


class InfraLagInterfaceL2(InfraInterface, InfraLagInterface, CoreArtifactTarget):
    l2_mode: String
    members: RelationshipManager
    untagged_vlan: RelatedNode
    tagged_vlan: RelationshipManager


class InfraLagInterfaceL3(InfraInterface, InfraLagInterface, CoreArtifactTarget):
    members: RelationshipManager
    ip_addresses: RelationshipManager


class OrganizationManufacturer(OrganizationGeneric):
    platform: RelationshipManager


class InfraMlagDomain(CoreNode):
    name: String
    domain_id: Integer
    devices: RelationshipManager
    peer_interfaces: RelationshipManager


class InfraMlagInterfaceL2(InfraMlagInterface):
    members: RelationshipManager


class InfraMlagInterfaceL3(InfraMlagInterface):
    members: RelationshipManager


class InfraPlatform(CoreNode):
    name: String
    description: StringOptional
    nornir_platform: StringOptional
    napalm_driver: StringOptional
    netmiko_device_type: StringOptional
    ansible_network_os: StringOptional
    devices: RelationshipManager


class OrganizationProvider(OrganizationGeneric):
    location: RelationshipManager
    circuit: RelationshipManager


class LocationRack(LocationGeneric):
    name: String
    description: StringOptional
    height: String
    facility_id: StringOptional
    serial_number: StringOptional
    asset_tag: StringOptional
    status: Dropdown
    role: DropdownOptional
    site: RelatedNode
    tags: RelationshipManager


class LocationSite(LocationGeneric):
    city: StringOptional
    address: StringOptional
    contact: StringOptional
    devices: RelationshipManager
    vlans: RelationshipManager
    circuit_endpoints: RelationshipManager
    tags: RelationshipManager


class OrganizationTenant(OrganizationGeneric):
    location: RelationshipManager
    circuit: RelationshipManager


class InfraVLAN(CoreNode):
    name: String
    description: StringOptional
    vlan_id: Integer
    status: Dropdown
    role: Dropdown
    site: RelatedNode
    gateway: RelatedNode
