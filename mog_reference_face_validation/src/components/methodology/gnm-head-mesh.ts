/**
 * Reduced neutral head-and-neck surface derived from Google GNM v3.0.
 * Source: https://github.com/google/GNM/tree/main/gnm/shape/data/versions/v3_0
 * License: Apache-2.0. The reduction and quantization are Mog-specific.
 */
import { GNM_POSITION_DATA } from "./gnm-head-mesh-positions";
import { GNM_TRIANGLES_1 } from "./gnm-head-mesh-triangles-1";
import { GNM_TRIANGLES_2 } from "./gnm-head-mesh-triangles-2";
import { GNM_TRIANGLES_3 } from "./gnm-head-mesh-triangles-3";

export const GNM_HEAD_MESH = {
  source: "Google GNM v3.0 head template",
  license: "Apache-2.0",
  vertexCount: GNM_POSITION_DATA.vertexCount,
  triangleCount: 1775,
  minimum: GNM_POSITION_DATA.minimum,
  maximum: GNM_POSITION_DATA.maximum,
  positionsBase64: GNM_POSITION_DATA.base64,
  trianglesBase64: GNM_TRIANGLES_1 + GNM_TRIANGLES_2 + GNM_TRIANGLES_3,
  landmarkVertexIndices: [479, 476, 752, 702, 638, 551, 468, 820, 822, 823, 755, 703, 641, 552, 469, 477, 480, 798, 864, 865, 866, 866, 867, 867, 868, 869, 801, 861, 891, 891, 892, 842, 842, 887, 843, 843, 791, 858, 859, 793, 859, 858, 794, 862, 863, 796, 863, 862, 835, 836, 884, 885, 885, 837, 838, 838, 883, 883, 882, 836, 835, 836, 885, 837, 838, 837, 883, 836] as const,
} as const;

function decodeUint16(base64: string): Uint16Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return new Uint16Array(bytes.buffer);
}

export type GnmVertex = { x: number; y: number; z: number };
export type GnmTriangle = readonly [number, number, number];

export function decodeGnmHeadMesh(): { vertices: GnmVertex[]; triangles: GnmTriangle[] } {
  const quantized = decodeUint16(GNM_HEAD_MESH.positionsBase64);
  const indices = decodeUint16(GNM_HEAD_MESH.trianglesBase64);
  if (quantized.length !== GNM_HEAD_MESH.vertexCount * 3) {
    throw new Error(`GNM position payload has ${quantized.length} values; expected ${GNM_HEAD_MESH.vertexCount * 3}.`);
  }
  if (indices.length !== GNM_HEAD_MESH.triangleCount * 3) {
    throw new Error(`GNM triangle payload has ${indices.length} values; expected ${GNM_HEAD_MESH.triangleCount * 3}.`);
  }
  const span = GNM_HEAD_MESH.maximum.map((value, axis) => value - GNM_HEAD_MESH.minimum[axis]);
  const vertices = Array.from({ length: GNM_HEAD_MESH.vertexCount }, (_, index) => ({
    x: GNM_HEAD_MESH.minimum[0] + quantized[index * 3] / 65535 * span[0],
    y: GNM_HEAD_MESH.minimum[1] + quantized[index * 3 + 1] / 65535 * span[1],
    z: GNM_HEAD_MESH.minimum[2] + quantized[index * 3 + 2] / 65535 * span[2],
  }));
  const triangles = Array.from({ length: GNM_HEAD_MESH.triangleCount }, (_, index) => [
    indices[index * 3], indices[index * 3 + 1], indices[index * 3 + 2],
  ] as const);
  return { vertices, triangles };
}
