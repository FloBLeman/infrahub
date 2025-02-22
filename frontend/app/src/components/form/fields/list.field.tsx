import { LabelFormField } from "@/components/form/fields/common";
import { FormFieldProps } from "@/components/form/type";
import { updateFormFieldValue } from "@/components/form/utils/updateFormFieldValue";
import List from "@/components/list";
import { FormField, FormInput, FormMessage } from "@/components/ui/form";

const ListField = ({
  defaultValue,
  description,
  label,
  name,
  rules,
  unique,
  ...props
}: FormFieldProps) => {
  return (
    <FormField
      key={name}
      name={name}
      rules={rules}
      defaultValue={defaultValue}
      render={({ field }) => {
        const fieldData = field.value;

        return (
          <div className="space-y-2">
            <LabelFormField
              label={label}
              unique={unique}
              required={!!rules?.required}
              description={description}
              fieldData={fieldData}
            />

            <FormInput>
              <List
                isProtected={props.disabled}
                {...field}
                value={fieldData?.value ?? ""}
                onChange={(newValue) => {
                  field.onChange(updateFormFieldValue(newValue, defaultValue));
                }}
                {...props}
              />
            </FormInput>

            <FormMessage />
          </div>
        );
      }}
    />
  );
};

export default ListField;
