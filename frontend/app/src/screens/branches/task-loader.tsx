import { TASK_OBJECT } from "@/config/constants";
import { TASK_DETAILS } from "@/graphql/queries/tasks/getTaskDetails";
import useQuery from "@/hooks/useQuery";
import ErrorScreen from "../errors/error-screen";
import LoadingScreen from "../loading-screen/loading-screen";

interface TaskLoaderProps {
  id: string;
}

export function TaskLoader({ id }: TaskLoaderProps) {
  const { error, data } = useQuery(TASK_DETAILS, { variables: { id } });

  if (error) {
    return <ErrorScreen message="An error occured while retrieving the task details." />;
  }

  if (data && data[TASK_OBJECT]?.count !== 0) {
    return <LoadingScreen message={"In progress"} />;
  }

  return <div>DONE</div>;
}
