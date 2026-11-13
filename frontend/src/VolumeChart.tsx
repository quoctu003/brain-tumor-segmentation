export default function VolumeChart({
  volumes,
}: {
  volumes: Record<string, number>;
}) {
  const regions = [
    { key: "wt", label: "WT", color: "#66dcc3" },
    { key: "tc", label: "TC", color: "#b29ad4" },
    { key: "et", label: "ET", color: "#fabc53" },
  ];
  const max = Math.max(1, ...regions.map((region) => volumes[region.key] ?? 0));
  return (
    <figure className="tw:mx-0 tw:my-5" aria-label="Biểu đồ thể tích phân đoạn">
      <figcaption className="tw:mb-3 tw:text-[10px] tw:tracking-wide tw:text-slate-400">
        SO SÁNH THỂ TÍCH · cm³
      </figcaption>
      <svg
        viewBox="0 0 280 120"
        className="tw:block tw:w-full"
        role="img"
        aria-labelledby="volumes-chart-title"
      >
        <title id="volumes-chart-title">
          {regions
            .map(
              (region) =>
                `${region.label}: ${(volumes[region.key] ?? 0).toFixed(2)} cm³`,
            )
            .join("; ")}
        </title>
        {regions.map((region, index) => (
          <g key={region.key} transform={`translate(0 ${index * 37 + 10})`}>
            <text x="0" y="14" fill="#99b8ad" fontSize="10">
              {region.label}
            </text>
            <rect
              x="29"
              y="2"
              width="179"
              height="15"
              rx="3"
              fill="#ffffff09"
            />
            <rect
              x="29"
              y="2"
              width={Math.max(0, ((volumes[region.key] ?? 0) / max) * 179)}
              height="15"
              rx="3"
              fill={region.color}
              opacity="0.8"
            />
            <text x="278" y="14" textAnchor="end" fill="#d0ddd7" fontSize="10">
              {(volumes[region.key] ?? 0).toFixed(2)}
            </text>
          </g>
        ))}
      </svg>
    </figure>
  );
}
