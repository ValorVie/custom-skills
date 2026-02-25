import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import YAML from "yaml";

export async function readYaml<T = unknown>(
  filePath: string,
): Promise<T | null> {
  try {
    const content = await readFile(filePath, "utf8");
    const parsed = YAML.parse(content);
    return (parsed ?? null) as T | null;
  } catch (error) {
    const err = error as NodeJS.ErrnoException;
    if (err.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

export async function writeYaml(
  filePath: string,
  data: unknown,
): Promise<void> {
  await mkdir(dirname(filePath), { recursive: true });
  await writeFile(filePath, YAML.stringify(data), "utf8");
}
