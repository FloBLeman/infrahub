import Accordion from "@/components/display/accordion";
import { classNames } from "@/utils/common";
import { Icon } from "@iconify-icon/react";
import { ReactElement } from "react";

type tUnauthorized = {
  className?: string;
  message?: string;
  icon?: ReactElement;
};

const DEFAULT_MESSAGE = "Sorry, you are not authorized to access this view.";

export default function UnauthorizedScreen({ className, message, icon }: tUnauthorized) {
  return (
    <div className={classNames("flex flex-col flex-1 items-center justify-center p-8", className)}>
      {icon || (
        <Icon
          icon={"mdi:warning-circle-outline"}
          className="bg-custom-white rounded-full text-red-300 text-3xl"
        />
      )}

      <Accordion
        title={"You can't access this view"}
        className="flex flex-col items-center w-full text-center"
      >
        <div>{message ?? DEFAULT_MESSAGE}</div>
      </Accordion>
    </div>
  );
}
