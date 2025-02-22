import LoadingScreen from "@/screens/loading-screen/loading-screen";
import { classNames } from "@/utils/common";
import { Icon } from "@iconify-icon/react";
import { ReactNode } from "react";

type tPill = {
  type?: PILL_TYPES;
  className?: string;
  children?: ReactNode;
  isLoading?: boolean;
  error?: boolean;
};

export enum PILL_TYPES {
  VALIDATE,
  CANCEL,
  WARNING,
}

const DEFAULT_CLASS = (className?: string) => `
  ${className?.includes("text") ? "" : "text-xs"}
  flex items-center
  flex-shrink-0 rounded-full px-2 py-0.5
  text-gray-80
`;

const getClassName = (type?: PILL_TYPES) => {
  switch (type) {
    case PILL_TYPES.VALIDATE: {
      return "bg-green-100 ";
    }
    case PILL_TYPES.CANCEL: {
      return "bg-red-100";
    }
    case PILL_TYPES.WARNING: {
      return "bg-yellow-100";
    }
    default: {
      return "bg-gray-100";
    }
  }
};

export const Pill = (props: tPill) => {
  const { type, className = "", children, isLoading, error } = props;

  const customClassName = getClassName(type);

  return (
    <span className={classNames(DEFAULT_CLASS(className), customClassName, className)}>
      {isLoading && <LoadingScreen size={8} hideText />}
      {error && <Icon icon={"mdi:warning-outline"} />}
      {!isLoading && children}
    </span>
  );
};
