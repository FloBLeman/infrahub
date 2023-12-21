export const artifactThreadSchema = [
  {
    id: "17a28ecc-a776-f84c-3873-c512f0a25a7c",
    name: "ArtifactThread",
    namespace: "Core",
    description: "A thread related to an artifact on a proposed change",
    default_filter: null,
    branch: "agnostic",
    order_by: null,
    display_labels: null,
    attributes: [
      {
        id: "17a28ecc-a80f-0185-3871-c5118f1ad43f",
        name: "artifact_id",
        kind: "Text",
        label: "Artifact Id",
        description: null,
        default_value: null,
        enum: null,
        regex: null,
        max_length: null,
        min_length: null,
        read_only: false,
        inherited: false,
        unique: false,
        branch: "agnostic",
        optional: true,
        order_weight: 1000,
        choices: null,
      },
      {
        id: "17a28ecc-a8a3-1007-3879-c51002d098ff",
        name: "storage_id",
        kind: "Text",
        label: "Storage Id",
        description: null,
        default_value: null,
        enum: null,
        regex: null,
        max_length: null,
        min_length: null,
        read_only: false,
        inherited: false,
        unique: false,
        branch: "agnostic",
        optional: true,
        order_weight: 2000,
        choices: null,
      },
      {
        id: "17a28ecc-a977-1b8e-387d-c5137718a465",
        name: "line_number",
        kind: "Number",
        label: "Line Number",
        description: null,
        default_value: null,
        enum: null,
        regex: null,
        max_length: null,
        min_length: null,
        read_only: false,
        inherited: false,
        unique: false,
        branch: "agnostic",
        optional: true,
        order_weight: 3000,
        choices: null,
      },
      {
        id: "17a28ecc-aa08-a9ed-3870-c51e798804ba",
        name: "label",
        kind: "Text",
        label: "Label",
        description: null,
        default_value: null,
        enum: null,
        regex: null,
        max_length: null,
        min_length: null,
        read_only: false,
        inherited: true,
        unique: false,
        branch: "agnostic",
        optional: true,
        order_weight: 4000,
        choices: null,
      },
      {
        id: "17a28ecc-aaa2-f5ed-3870-c51bb0dede63",
        name: "resolved",
        kind: "Boolean",
        label: "Resolved",
        description: null,
        default_value: false,
        enum: null,
        regex: null,
        max_length: null,
        min_length: null,
        read_only: false,
        inherited: true,
        unique: false,
        branch: "agnostic",
        optional: true,
        order_weight: 5000,
        choices: null,
      },
      {
        id: "17a28ecc-ab39-83c1-3871-c51198bc8704",
        name: "created_at",
        kind: "DateTime",
        label: "Created At",
        description: null,
        default_value: null,
        enum: null,
        regex: null,
        max_length: null,
        min_length: null,
        read_only: false,
        inherited: true,
        unique: false,
        branch: "agnostic",
        optional: true,
        order_weight: 6000,
        choices: null,
      },
    ],
    relationships: [
      {
        id: "17a28ecc-abd1-f0c0-3876-c51693b29195",
        name: "change",
        peer: "CoreProposedChange",
        kind: "Parent",
        direction: "bidirectional",
        label: "Change",
        description: null,
        identifier: "proposedchange__thread",
        inherited: true,
        cardinality: "one",
        branch: "agnostic",
        optional: false,
        filters: [
          {
            name: "ids",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "source_branch__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "source_branch__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "source_branch__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "source_branch__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "source_branch__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "source_branch__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "destination_branch__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "destination_branch__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "destination_branch__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "destination_branch__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "destination_branch__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "destination_branch__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "state__value",
            kind: "Text",
            enum: ["open", "merged", "closed", "canceled"],
            object_kind: null,
            description: null,
          },
          {
            name: "state__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "state__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "state__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "state__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "state__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
        ],
        order_weight: 7000,
      },
      {
        id: "17a28ecc-ac5c-fdeb-3874-c5129ae22d5c",
        name: "comments",
        peer: "CoreThreadComment",
        kind: "Component",
        direction: "bidirectional",
        label: "Comments",
        description: null,
        identifier: "thread__threadcomment",
        inherited: true,
        cardinality: "many",
        branch: "agnostic",
        optional: true,
        filters: [
          {
            name: "ids",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
        ],
        order_weight: 8000,
      },
      {
        id: "17a28ecc-acea-ce9b-387f-c516aa28947a",
        name: "created_by",
        peer: "CoreAccount",
        kind: "Generic",
        direction: "bidirectional",
        label: "Created By",
        description: null,
        identifier: "coreaccount__corethread",
        inherited: true,
        cardinality: "one",
        branch: "agnostic",
        optional: true,
        filters: [
          {
            name: "ids",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "type__value",
            kind: "Text",
            enum: ["User", "Script", "Bot", "Git"],
            object_kind: null,
            description: null,
          },
          {
            name: "type__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "type__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "type__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "type__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "type__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "role__value",
            kind: "Text",
            enum: ["admin", "read-only", "read-write"],
            object_kind: null,
            description: null,
          },
          {
            name: "role__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "role__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "role__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "role__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "role__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
        ],
        order_weight: 9000,
      },
      {
        id: "17a28ecc-b0e0-e2c6-3877-c512de8ae841",
        name: "member_of_groups",
        peer: "CoreGroup",
        kind: "Group",
        direction: "bidirectional",
        label: "Member Of Groups",
        description: null,
        identifier: "group_member",
        inherited: false,
        cardinality: "many",
        branch: "aware",
        optional: true,
        filters: [
          {
            name: "ids",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
        ],
        order_weight: 10000,
      },
      {
        id: "17a28ecc-b1a1-2027-3870-c516e3cd7da6",
        name: "subscriber_of_groups",
        peer: "CoreGroup",
        kind: "Group",
        direction: "bidirectional",
        label: "Subscriber Of Groups",
        description: null,
        identifier: "group_subscriber",
        inherited: false,
        cardinality: "many",
        branch: "aware",
        optional: true,
        filters: [
          {
            name: "ids",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "name__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "label__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__value",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__values",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__is_visible",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__is_protected",
            kind: "Boolean",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__source__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
          {
            name: "description__owner__id",
            kind: "Text",
            enum: null,
            object_kind: null,
            description: null,
          },
        ],
        order_weight: 11000,
      },
    ],
    filters: [
      {
        name: "ids",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "artifact_id__value",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "artifact_id__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "artifact_id__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "artifact_id__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "artifact_id__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "artifact_id__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "storage_id__value",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "storage_id__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "storage_id__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "storage_id__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "storage_id__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "storage_id__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "line_number__value",
        kind: "Number",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "line_number__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "line_number__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "line_number__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "line_number__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "line_number__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "label__value",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "label__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "label__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "label__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "label__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "label__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "resolved__value",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "resolved__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "resolved__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "resolved__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "resolved__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "resolved__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "any__value",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "any__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "any__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "any__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "any__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__ids",
        kind: "Text",
        enum: null,
        object_kind: "CoreProposedChange",
        description: null,
      },
      {
        name: "change__name__value",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__name__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__name__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__name__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__name__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__name__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__source_branch__value",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__source_branch__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__source_branch__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__source_branch__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__source_branch__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__source_branch__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__destination_branch__value",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__destination_branch__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__destination_branch__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__destination_branch__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__destination_branch__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__destination_branch__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__state__value",
        kind: "Text",
        enum: ["open", "merged", "closed", "canceled"],
        object_kind: null,
        description: null,
      },
      {
        name: "change__state__values",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__state__is_visible",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__state__is_protected",
        kind: "Boolean",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__state__source__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
      {
        name: "change__state__owner__id",
        kind: "Text",
        enum: null,
        object_kind: null,
        description: null,
      },
    ],
    include_in_menu: false,
    menu_placement: null,
    icon: null,
    label: "Thread - Artifact",
    inherit_from: ["CoreThread"],
    groups: [],
    kind: "CoreArtifactThread",
    hash: "adcda35f06aac1e7ae1daee318c2140b",
  },
];

export const artifactThreadMockQuery = `query {
  CoreArtifactThread(change__ids: "1cec1fe9-fcc4-4f5b-af30-9d661de65bd8&amp;pr_tab&#x3D;artifacts") {
    count
    edges {
      node {
        id
        display_label
        __typename
        _updated_at

        line_number {
          value
        }

        storage_id {
          value
        }

        resolved {
          value
        }

        comments {
          edges {
            node {
              id

              text {
                value
              }

              created_by {
                node {
                  display_label
                }
              }

              created_at {
                value
              }
            }
          }
        }
      }
    }
  }
}
`;

export const artifactThreadMockData = {
  CoreArtifactThread: {
    count: 2,
    edges: [
      {
        node: {
          id: "17a2dac5-6ee6-690c-3879-c51278c3db0a",
          display_label: "CoreArtifactThread(ID: 17a2dac5-6ee6-690c-3879-c51278c3db0a)",
          __typename: "CoreArtifactThread",
          _updated_at: "2023-12-21T13:09:10.606650+00:00",
          line_number: {
            value: 35,
            __typename: "NumberAttribute",
          },
          storage_id: {
            value: "17a28ff2-526c-2f68-3876-c511fd22b9e3",
            __typename: "TextAttribute",
          },
          resolved: {
            value: false,
            __typename: "CheckboxAttribute",
          },
          comments: {
            edges: [
              {
                node: {
                  id: "17a2dac5-7755-01cc-3876-c51eb6604209",
                  text: {
                    value: "comment on new line",
                    __typename: "TextAttribute",
                  },
                  created_by: {
                    node: {
                      display_label: "Admin",
                      __typename: "CoreAccount",
                    },
                    __typename: "NestedEdgedCoreAccount",
                  },
                  created_at: {
                    value: "2023-12-21T14:09:10+01:00",
                    __typename: "TextAttribute",
                  },
                  __typename: "CoreThreadComment",
                },
                __typename: "NestedEdgedCoreThreadComment",
              },
            ],
            __typename: "NestedPaginatedCoreThreadComment",
          },
        },
        __typename: "EdgedCoreArtifactThread",
      },
      {
        node: {
          id: "17a2dac6-8735-fbbd-387e-c510cd5400f7",
          display_label: "CoreArtifactThread(ID: 17a2dac6-8735-fbbd-387e-c510cd5400f7)",
          __typename: "CoreArtifactThread",
          _updated_at: "2023-12-21T13:09:15.307479+00:00",
          line_number: {
            value: 36,
            __typename: "NumberAttribute",
          },
          storage_id: {
            value: "17a28f63-f0bb-b131-3875-c51eff1b7a20",
            __typename: "TextAttribute",
          },
          resolved: {
            value: false,
            __typename: "CheckboxAttribute",
          },
          comments: {
            edges: [
              {
                node: {
                  id: "17a2dac6-8e6c-75fb-387a-c518bcd63b28",
                  text: {
                    value: "comment on old line",
                    __typename: "TextAttribute",
                  },
                  created_by: {
                    node: {
                      display_label: "Admin",
                      __typename: "CoreAccount",
                    },
                    __typename: "NestedEdgedCoreAccount",
                  },
                  created_at: {
                    value: "2023-12-21T14:09:15+01:00",
                    __typename: "TextAttribute",
                  },
                  __typename: "CoreThreadComment",
                },
                __typename: "NestedEdgedCoreThreadComment",
              },
            ],
            __typename: "NestedPaginatedCoreThreadComment",
          },
        },
        __typename: "EdgedCoreArtifactThread",
      },
    ],
    __typename: "PaginatedCoreArtifactThread",
  },
};
export const artifactWithoutThreadMockData = {
  CoreArtifactThread: {
    count: 0,
    edges: [],
    __typename: "PaginatedCoreArtifactThread",
  },
};
