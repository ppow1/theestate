const COLORS = {
  green: "#18a558",
  yellow: "#d6b03f",
  orange: "#e07322",
  blue: "#2986cc",
  red: "#c73535",
  gray: "#6b7280",
  off: "#3f4652"
};

function escapeXml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function serviceSegments(status) {
  const services = status.raw?.services;
  if (!Array.isArray(services) || services.length === 0) {
    return "";
  }

  const gap = 4;
  const availableWidth = 110;
  const width = Math.max(10, Math.floor((availableWidth - gap * (services.length - 1)) / services.length));
  const startX = Math.floor((144 - (width * services.length + gap * (services.length - 1))) / 2);
  return services
    .map((service, index) => {
      const x = startX + index * (width + gap);
      const fill = service.online ? COLORS.green : COLORS.off;
      const stroke = service.online ? "#62d58f" : "#697180";
      return `<rect x="${x}" y="116" width="${width}" height="12" rx="3" fill="${fill}" stroke="${stroke}" stroke-width="1"/>`;
    })
    .join("");
}

function perimeterSegments(status) {
  const services = status.raw?.services;
  if (!Array.isArray(services) || services.length < 3) {
    return "";
  }

  const [top, right, bottom] = services;
  const leftFill = COLORS[status.raw?.aggregateColor] || COLORS[status.color] || COLORS.gray;
  const parts = [
    { x: 46, y: 14, width: 52, height: 10, service: top },
    { x: 120, y: 44, width: 10, height: 52, service: right },
    { x: 46, y: 120, width: 52, height: 10, service: bottom }
  ];
  const rendered = parts
    .map(({ x, y, width, height, service }) => {
      const fill = service.online ? COLORS.green : COLORS.off;
      const stroke = service.online ? "#62d58f" : "#697180";
      return `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="3" fill="${fill}" stroke="${stroke}" stroke-width="1"/>`;
    })
    .join("");
  return `${rendered}<rect x="14" y="44" width="10" height="52" rx="3" fill="${leftFill}" stroke="#8b94a5" stroke-width="1"/>`;
}

export function renderKeyImage(action, status) {
  const accent = COLORS[status.color] || COLORS.gray;
  const label = escapeXml(action.label);
  const value = escapeXml(status.value || "...");
  const hasSegments = Array.isArray(status.raw?.services) && status.raw.services.length > 0;
  const usePerimeter = action.key === "startEstateSurfaces" && status.raw?.services?.length >= 3;
  const valueSize = value.length > 7 ? 24 : value.length > 5 ? 28 : 38;
  const valueY = hasSegments ? (usePerimeter ? 82 : 86) : 92;
  const segments = usePerimeter ? perimeterSegments(status) : serviceSegments(status);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144">
  <rect width="144" height="144" rx="12" fill="#101318"/>
  <rect x="8" y="8" width="128" height="128" rx="10" fill="#151a21" stroke="${accent}" stroke-width="8"/>
  <rect x="17" y="17" width="110" height="25" rx="4" fill="${accent}"/>
  <text x="72" y="36" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-size="18" font-weight="700" text-anchor="middle">${label}</text>
  <text x="72" y="${valueY}" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-size="${valueSize}" font-weight="800" text-anchor="middle">${value}</text>
  ${segments}
</svg>`;
  return `data:image/svg+xml;base64,${Buffer.from(svg, "utf8").toString("base64")}`;
}

export function manifestIconSvg(label, color = "blue") {
  const accent = COLORS[color] || COLORS.blue;
  const safeLabel = escapeXml(label);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144">
  <rect width="144" height="144" rx="12" fill="#101318"/>
  <rect x="10" y="10" width="124" height="124" rx="10" fill="#151a21" stroke="${accent}" stroke-width="8"/>
  <text x="72" y="84" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="800" text-anchor="middle">${safeLabel}</text>
</svg>`;
}



