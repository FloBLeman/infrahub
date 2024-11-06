import { TASK_OBJECT } from "@/config/constants";
import useQuery from "@/hooks/useQuery";
import { gql } from "@apollo/client";

import { DateDisplay } from "@/components/display/date-display";
import { List } from "@/components/table/list";
import { Badge } from "@/components/ui/badge";
import { Id } from "@/components/ui/id";
import { SearchInput } from "@/components/ui/search-input";
import { QSP } from "@/config/qsp";
import { getTaskItemDetails } from "@/graphql/queries/tasks/getTasksItemDetails";
import ErrorScreen from "@/screens/errors/error-screen";
import LoadingScreen from "@/screens/loading-screen/loading-screen";
import { forwardRef, useImperativeHandle, useState } from "react";
import { useParams } from "react-router-dom";
import { StringParam, useQueryParam } from "use-query-params";
import { Logs, tLog } from "./logs";

export const getStateBadge: { [key: string]: any } = {
  SCHEDULED: <Badge variant={"blue"}>SCHEDULED</Badge>,
  PENDING: <Badge variant={"blue-outline"}>PENDING</Badge>,
  RUNNING: <Badge variant={"green-outline"}>RUNNING</Badge>,
  COMPLETED: <Badge variant={"green"}>COMPLETED</Badge>,
  FAILED: <Badge variant={"red"}>FAILED</Badge>,
  CANCELLED: <Badge variant={"red-outline"}>CANCELLED</Badge>,
  CRASHED: <Badge variant={"yellow"}>CRASHED</Badge>,
  PAUSED: <Badge variant={"blue-outline"}>PAUSED</Badge>,
  CANCELLING: <Badge variant={"gray"}>CANCELLING</Badge>,
};

interface TaskItemDetailsProps {
  id?: string;
  pollInterval?: number;
}

export const TaskItemDetails = forwardRef(({ id, pollInterval }: TaskItemDetailsProps, ref) => {
  const [idFromQsp] = useQueryParam(QSP.TASK_ID, StringParam);
  const [search, setSearch] = useState("");

  const { task: idFromParams } = useParams();

  const queryString = getTaskItemDetails({
    kind: TASK_OBJECT,
    id: id || idFromParams || idFromQsp,
  });

  const query = gql`
    ${queryString}
  `;

  const { loading, error, data = {}, refetch } = useQuery(query, { pollInterval });

  // Provide refetch function to parent
  useImperativeHandle(ref, () => ({ refetch }));

  if (error) {
    return <ErrorScreen message="Something went wrong when fetching list." />;
  }

  if (loading) {
    return <LoadingScreen message="Loading task..." />;
  }

  const result = data ? (data[TASK_OBJECT] ?? {}) : {};

  const { edges = [] } = result;

  const columns = [
    {
      name: "id",
      label: "ID",
    },
    {
      name: "title",
      label: "Title",
    },
    {
      name: "state",
      label: "State",
    },
    {
      name: "related_node",
      label: "Related node",
    },
    {
      name: "progress",
      label: "Progress",
    },
    {
      name: "updated_at",
      label: "Updated at",
    },
  ];

  const object = edges[0].node;

  const row = {
    values: {
      id: object.id,
      title: object.title,
      state: getStateBadge[object.state],
      related_node: object.related_node_kind && (
        <Id id={object.related_node} kind={object.related_node_kind} preventCopy />
      ),
      progress: object.progress,
      updated_at: <DateDisplay date={object.updated_at} />,
    },
  };

  const logs = object.logs.edges
    .map((edge: any) => edge.node)
    .filter((log: tLog) => {
      if (!search) return true;

      return (
        log.message?.includes(search) || log.severity?.includes(search) || log.id?.includes(search)
      );
    });

  const count = logs.length;

  return (
    <div className=" flex-1 flex flex-col">
      <div className="bg-custom-white">
        <List columns={columns} row={row} />
      </div>

      <div className="rounded-md overflow-hidden bg-custom-white m-4 p-2">
        <div className="flex mb-2">
          <h2 className="flex-1 font-semibold text-gray-900 m-2 ml-0">Task Logs ({count})</h2>

          <div className="flex flex-1 justify-end">
            <SearchInput
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search logs from message or severity"
              className="min-w-96"
            />
          </div>
        </div>

        <Logs logs={logs} />
      </div>
    </div>
  );
});
