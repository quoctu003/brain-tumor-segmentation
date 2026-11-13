const stack = [
  ["Frontend", "React + Vite + Tailwind CSS"],
  ["Backend", "Python + FastAPI"],
  ["AI", "PyTorch + MONAI · 3D U-Net"],
  ["Database", "PostgreSQL + SQLAlchemy"],
  ["MRI Viewer", "NiiVue · NIfTI 2D/3D"],
  ["Xử lý MRI", "NiBabel + NumPy"],
  ["Báo cáo", "PDF + biểu đồ thể tích"],
  ["Môi trường", "VS Code · Python · Node.js"],
];

export default function TechStack() {
  return (
    <section
      className="tw:my-6 tw:rounded-xl tw:border tw:border-white/10 tw:bg-[#171c22] tw:p-6"
      aria-labelledby="tech-stack-title"
    >
      <div className="tw:mb-5 tw:flex tw:flex-wrap tw:items-center tw:justify-between tw:gap-3">
        <h2 id="tech-stack-title">Kiến trúc & công nghệ</h2>
        <span className="tw:rounded-full tw:border tw:border-emerald-300/20 tw:px-3 tw:py-1 tw:text-[10px] tw:tracking-wider tw:text-emerald-200">
          RESEARCH WORKSPACE
        </span>
      </div>
      <div className="tw:overflow-x-auto">
        <table className="tw:w-full tw:border-collapse tw:text-left tw:text-xs">
          <thead>
            <tr className="tw:border-b tw:border-white/10 tw:text-slate-400">
              <th className="tw:py-3 tw:pr-5 tw:font-medium" scope="col">
                Thành phần
              </th>
              <th className="tw:py-3 tw:font-medium" scope="col">
                Công nghệ
              </th>
            </tr>
          </thead>
          <tbody>
            {stack.map(([name, technology]) => (
              <tr key={name} className="tw:border-b tw:border-white/5">
                <th
                  scope="row"
                  className="tw:py-3 tw:pr-5 tw:font-normal tw:text-slate-400"
                >
                  {name}
                </th>
                <td className="tw:py-3 tw:leading-6 tw:text-slate-200">
                  {technology}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="tw:mb-0 tw:mt-4 tw:text-[11px] tw:leading-7 tw:text-slate-400">
        PostgreSQL dùng cho chế độ triển khai qua Docker. Bản local dùng SQLite
        + SQLAlchemy để mở được trên máy chưa có PostgreSQL hoặc Docker.
      </p>
    </section>
  );
}
