import { FieldValues, RegisterOptions, UseFormRegister, UseFormSetValue } from "react-hook-form";
import { FormFieldError } from "../screens/edit-form-hook/form";
import { OpsInput } from "./input";

interface Props {
  inputType: string;
  name: string;
  label: string;
  value: string;
  register: UseFormRegister<FieldValues>;
  config?: RegisterOptions<FieldValues, string> | undefined;
  setValue: UseFormSetValue<FieldValues>;
  error?: FormFieldError;
}

export const OpsInputRegister = (props: Props) => {
  const { name, value, register, setValue, config, label, error, inputType } = props;

  const inputRegister = register(name, {
    value: value ?? "",
    ...config,
  });

  return (
    <OpsInput
      type={inputType}
      label={label}
      value={value}
      onChange={(value) => setValue(inputRegister.name, value)}
      error={error}
    />
  );
};
