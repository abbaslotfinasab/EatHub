// TopBar.tsx
export default function TopBar() {
    return (
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50">

            {/* Left */}
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-green-900" />
                <span className="font-semibold text-gray-800">EatHub Dashboard</span>
            </div>

            {/* Center - Restaurant Selector */}
            <select className="px-3 py-1 rounded-lg border text-sm bg-white">
                <option>Central Branch</option>
                <option>North Branch</option>
            </select>

            {/* Right */}
            <div className="flex items-center gap-3">
        <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">
          Online
        </span>

                <button className="w-8 h-8 rounded-full bg-gray-200" />
            </div>
        </div>
    );
}