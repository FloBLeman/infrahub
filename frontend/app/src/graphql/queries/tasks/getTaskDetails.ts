import { gql } from "@apollo/client";

export const TASK_DETAILS = gql`
query GetTasks($id: String!) {
  InfrahubTask(ids: [$id]) {
    count
  }
}
`;
