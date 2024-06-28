import Ajv, { type JSONSchemaType } from "ajv";
import yaml from "js-yaml";

export type JSONSchema = {
  type: string;
  properties?: Record<string, JSONSchema>;
  items?: JSONSchema;
};

export function generateSchema(obj: any): JSONSchema {
  if (typeof obj !== "object" || obj === null) {
    return { type: typeof obj };
  }

  if (Array.isArray(obj)) {
    return {
      type: "array",
      items: generateSchema(obj[0])
    };
  }

  const properties: Record<string, JSONSchema> = {};
  for (const key in obj) {
    properties[key] = generateSchema(obj[key]);
  }

  return {
    type: "object",
    properties
  };
}

const ajv = new Ajv();

export function validateYaml(schema: JSONSchemaType<any>, data: any) {
  const validate = ajv.compile(schema);
  const valid = validate(data);
  if (!valid) {
    console.error(validate.errors);
  }
  return valid;
}

export function updateYaml(jsonData: Record<string, any>): string {
  return yaml.dump(jsonData);
}
