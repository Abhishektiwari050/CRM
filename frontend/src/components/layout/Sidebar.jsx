import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Bell, FileText, Settings, User, LogOut, Sun, Moon } from 'lucide-react';
import clsx from 'clsx';

const Sidebar = () => {
    // Get role from session storage or default to manager
    const getUserRole = () => {
        try {
            const user = JSON.parse(sessionStorage.getItem('currentUser'));
            return user?.role || 'manager';
        } catch {
            return 'manager';
        }
    };
    const role = getUserRole();

    const links = [
        { icon: LayoutDashboard, text: 'Dashboard', to: '/' },
        { icon: Users, text: 'All Clients', to: '/clients' },
        { icon: Bell, text: 'Notifications', to: '/notifications', badge: 0 },
        { icon: Settings, text: 'Team Management', to: '/team' },
        { icon: FileText, text: 'Reports', to: '/reports' }
    ];

    const [isDarkMode, setIsDarkMode] = React.useState(() => {
        // Default to Dark Mode (Blue Gradient) unless explicitly set to light
        return localStorage.getItem('sidebar-theme') !== 'light';
    });

    React.useEffect(() => {
        localStorage.setItem('sidebar-theme', isDarkMode ? 'dark' : 'light');
    }, [isDarkMode]);

    const toggleTheme = () => {
        setIsDarkMode(!isDarkMode);
    };

    const handleLogout = () => {
        sessionStorage.removeItem('token');
        window.location.href = '/login';
    };

    // Theme Classes
    const containerClasses = isDarkMode
        ? "bg-gradient-to-b from-blue-900 via-blue-800 to-indigo-900 border-white/10 text-white"
        : "bg-white border-slate-200 text-slate-800";

    const logoBg = isDarkMode ? "bg-white/10 border-white/20" : "bg-blue-50 border-blue-100";
    const logoIcon = isDarkMode ? "text-blue-200" : "text-blue-600";
    const brandText = isDarkMode ? "text-white" : "text-slate-800";
    const brandSub = isDarkMode ? "text-blue-200/80" : "text-slate-400";

    // Nav Item styles
    const getNavLinkClass = (isActive) => {
        if (isDarkMode) {
            return isActive
                ? "bg-white/15 text-white shadow-lg shadow-blue-900/20 border border-white/10"
                : "text-blue-100/70 hover:bg-white/5 hover:text-white";
        } else {
            return isActive
                ? "bg-blue-50 text-blue-700 font-semibold border border-blue-100 shadow-sm"
                : "text-slate-500 hover:bg-slate-50 hover:text-slate-900";
        }
    };

    // User Profile Area
    const profileBg = isDarkMode ? "bg-black/20 border-white/5" : "bg-slate-50 border-slate-100";
    const profileText = isDarkMode ? "text-white" : "text-slate-800";
    const profileSub = isDarkMode ? "text-blue-200/60" : "text-slate-500";

    const btnClass = isDarkMode
        ? "text-blue-100/80 hover:bg-white/10 hover:text-white"
        : "text-slate-500 hover:bg-slate-100 hover:text-slate-900";

    return (
        <div className={clsx("h-screen w-72 border-r flex flex-col fixed left-0 top-0 z-50 shadow-2xl transition-colors duration-300", containerClasses)}>
            {/* Logo */}
            <div className="p-8 pb-4">
                <div className="flex items-center gap-3">
                    <div className={clsx("w-10 h-10 backdrop-blur-sm rounded-xl flex items-center justify-center border shadow-inner transition-colors", logoBg)}>
                        <Users size={24} className={logoIcon} />
                    </div>
                    <div>
                        <h1 className={clsx("font-bold text-xl tracking-wide", brandText)}>Manager</h1>
                        <p className={clsx("text-xs font-medium tracking-wider", brandSub)}>PORTAL</p>
                    </div>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto custom-scrollbar">
                {links.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-200 group relative overflow-hidden",
                            getNavLinkClass(isActive)
                        )}
                    >
                        <item.icon size={20} className="relative z-10 transition-transform group-hover:scale-110 duration-200" />
                        <span className="relative z-10 font-medium tracking-wide text-sm">{item.text}</span>
                    </NavLink>
                ))}
            </nav>

            {/* User Profile */}
            <div className={clsx("p-4 m-4 mt-0 rounded-2xl border backdrop-blur-sm transition-colors", profileBg)}>
                <div className="flex items-center gap-3 mb-4 p-2">
                    <div className="w-10 h-10 rounded-full bg-white/10 p-0.5 shadow-lg overflow-hidden border-2 border-white/20">
                        <img
                            src="/manager_icon.png"
                            alt="Profile"
                            className="w-full h-full object-cover rounded-full"
                        />
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className={clsx("text-sm font-bold truncate", profileText)}>Manager</p>
                        <p className={clsx("text-xs truncate capitalize", profileSub)}>{role}</p>
                    </div>
                </div>

                <div className="space-y-1">
                    <button className={clsx("w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left group", btnClass)}>
                        <User size={20} />
                        <span className="text-sm font-medium">Profile</span>
                    </button>
                    <button
                        onClick={toggleTheme}
                        className={clsx("w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left group", btnClass)}
                    >
                        {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
                        <span className="text-sm font-medium">{isDarkMode ? 'Sidebar: Light' : 'Sidebar: Dark'}</span>
                    </button>
                    <button
                        onClick={handleLogout}
                        className={clsx("w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left group mt-4", isDarkMode ? "text-red-200/80 hover:bg-red-500/20 hover:text-red-100" : "text-red-500 hover:bg-red-50 hover:text-red-600")}
                    >
                        <LogOut size={20} />
                        <span className="text-sm font-medium">Logout</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
