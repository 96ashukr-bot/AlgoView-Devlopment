import React, { Fragment, useContext, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import SvgIcon from "../../Components/Common/Component/SvgIcon";
import CustomizerContext from "../../_helper/Customizer";
import { MENUITEMS} from "./Menu";
import { MENUITEMSNEW } from "./Menunewclients";
import { MENUITEMSNEWNEW} from "./Menunewnew";
import { fetchUserProfile, getSupportChatUnreadCount } from './../../Services/Authentication';

const SUPPORT_CHAT_BADGE_INTERVAL_MS = 30000;

const SidebarMenuItems = ({ setMainMenu, sidebartoogle, setNavActive, activeClass }) => {
  const { layout } = useContext(CustomizerContext);
  const layout1 = localStorage.getItem("sidebar_layout") || layout;

  const id = window.location.pathname.split("/").pop();
  const layoutId = id;
  const CurrentPath = window.location.pathname;
  const [supportChatUnreadCount, setSupportChatUnreadCount] = useState(0);

  useEffect(() => {
    const getUserProfile = async () => {
      try {
        const data = await fetchUserProfile();
        setUserProfile(data);
      } catch (error) {
        console.error("Error fetching user profile:", error);
      }
    };
    getUserProfile();


  }, []);

  useEffect(() => {
    let timeoutId;
    let cancelled = false;

    const refreshUnreadCount = async () => {
      if (cancelled || document.hidden) return;
      try {
        const data = await getSupportChatUnreadCount();
        setSupportChatUnreadCount(Number(data.unread_count || 0));
      } catch (_error) {
        setSupportChatUnreadCount(0);
      }
    };
    const scheduleRefresh = () => {
      timeoutId = window.setTimeout(async () => {
        await refreshUnreadCount();
        if (!cancelled) {
          scheduleRefresh();
        }
      }, SUPPORT_CHAT_BADGE_INTERVAL_MS);
    };
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        refreshUnreadCount();
      }
    };

    refreshUnreadCount();
    scheduleRefresh();
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);


  const [userProfile, setUserProfile] = useState({
    email: '',
    firstName: '',
    lastName: '',
    fullName: '',
    phoneNumber: '',
    PANEL_CLIENT_KEY: '',
    start_date: null,
    end_date: null,
    client_type: '',
    role: null
  });


  // const MENUITEMSSELECTION =  (userProfile.email == 'admin@yopmail.com') ? MENUITEMS : MENUITEMSNEW;
  const isSuperAdmin = userProfile.role && userProfile.role.name === "Super-Admin";
  const isAdmin = userProfile.role && userProfile.role.name === "Admin";
  const issubAdmin = userProfile.role && userProfile.role.name === "Sub-Admin";

  let menuItems;

  if (isAdmin || isSuperAdmin ) {
      menuItems = MENUITEMS;
  } else if (issubAdmin) {
      menuItems = MENUITEMSNEWNEW; 
  } else {
      menuItems = MENUITEMSNEW;
  }



  // const MENUITEMSSELECTION = isAdmin ? MENUITEMS : MENUITEMSNEW ? issubAdmin : MENUITEMSNEWNEW ;

  const { t } = useTranslation();
  const supportChatBadge = supportChatUnreadCount > 0 && !CurrentPath.includes("/support-chat")
    ? (
      <label className="badge bg-danger ms-2">
        {supportChatUnreadCount > 99 ? "99+" : supportChatUnreadCount}
      </label>
    )
    : null;

  const toggletNavActive = (item) => {
    if (window.innerWidth <= 991) {
      document.querySelector(".page-header").className = "page-header close_icon";
      document.querySelector(".sidebar-wrapper").className = "sidebar-wrapper close_icon ";
      document.querySelector(".bg-overlay1")?.classList.remove("active");
      document.body.classList.remove("sidebar-open");
      // document.querySelector('.mega-menu-container').classList.remove('d-block');
      if (item.type === "sub") {
        document.querySelector(".page-header").className = "page-header";
        document.querySelector(".sidebar-wrapper").className = "sidebar-wrapper";
        document.querySelector(".bg-overlay1")?.classList.add("active");
        document.body.classList.add("sidebar-open");
      }
    }
    if (!item.active) {
      menuItems.map((a) => {
        a.Items.filter((Items) => {
          if (a.Items.includes(item)) Items.active = false;
          if (!Items.children) return false;
          Items.children.forEach((b) => {
            if (Items.children.includes(item)) {
              b.active = false;
            }
            if (!b.children) return false;
            b.children.forEach((c) => {
              if (b.children.includes(item)) {
                c.active = false;
              }
            });
          });
          return Items;
        });
        return a;
      });
    }
    item.active = !item.active;
    setMainMenu({ mainmenu: menuItems });
  };

  return (
    <>
      {menuItems.map((Item, i) => (
        <Fragment key={i}>
          <li className="sidebar-main-title">
            <div>
              <h6 className="lan-1">{t(Item.menutitle)}</h6>
            </div>
          </li>
          {Item.Items.filter((menuItem) => isSuperAdmin || !menuItem.superadminOnly).map((menuItem, i) => (
            <li className="sidebar-list" key={i}>
              {menuItem.type === "sub" ? (
                <a
                  href="javascript"
                  className={`sidebar-link sidebar-title ${CurrentPath.includes(menuItem.title.toLowerCase()) ? "active" : ""} ${menuItem.active && "active"}`}
                  onClick={(event) => {
                    event.preventDefault();
                    setNavActive(menuItem);
                    activeClass(menuItem.active);
                  }}>
                  <SvgIcon className="stroke-icon" iconId={`stroke-${menuItem.icon}`} />
                  <SvgIcon className="fill-icon" iconId={`fill-${menuItem.icon}`} />
                  <span>{t(menuItem.title)}</span>
                  {menuItem.badge ? <label className={menuItem.badge}>{menuItem.badgetxt}</label> : ""}
                  <div className="according-menu">{menuItem.active ? <i className="fa fa-angle-down"></i> : <i className="fa fa-angle-right"></i>}</div>
                </a>
              ) : (
                ""
              )}

              {menuItem.type === "link" ? (
                <Link to={menuItem.path} className={`sidebar-link sidebar-title link-nav  ${CurrentPath.includes(menuItem.title.toLowerCase()) ? "active" : ""}`} onClick={() => toggletNavActive(menuItem)}>
                  <SvgIcon className="stroke-icon" iconId={`stroke-${menuItem.icon}`} />
                  <SvgIcon className="fill-icon" iconId={`fill-${menuItem.icon}`} />
                  <span>{t(menuItem.title)}</span>
                  {menuItem.path === "/support-chat" ? supportChatBadge : null}
                  {menuItem.badge ? <label className={menuItem.badge}>{menuItem.badgetxt}</label> : ""}
                </Link>
              ) : (
                ""
              )}

              {menuItem.children ? (
                <ul className="sidebar-submenu" style={layout1 !== "compact-sidebar compact-small" ? (menuItem?.active || CurrentPath.includes(menuItem?.title?.toLowerCase()) ? (sidebartoogle ? { opacity: 1, transition: "opacity 500ms ease-in" } : { display: "block" }) : { display: "none" }) : { display: "none" }}>
                  {menuItem.children.filter((childrenItem) => isSuperAdmin || !childrenItem.superadminOnly).map((childrenItem, index) => {
                    return (
                      <li key={index}>
                        {childrenItem.type === "sub" ? (
                          <a
                            href="javascript"
                            className={`${CurrentPath.includes(childrenItem?.title?.toLowerCase()) ? "active" : ""}`}
                            // className={`${childrenItem.active ? 'active' : ''}`}
                            onClick={(event) => {
                              event.preventDefault();
                              toggletNavActive(childrenItem);
                            }}>
                            {t(childrenItem.title)}
                            <span className="sub-arrow">
                              <i className="fa fa-chevron-right"></i>
                            </span>
                            <div className="according-menu">{childrenItem.active ? <i className="fa fa-angle-down"></i> : <i className="fa fa-angle-right"></i>}</div>
                          </a>
                        ) : (
                          ""
                        )}

                        {childrenItem.type === "link" ? (
                          <Link
                            to={childrenItem.path}
                            className={`${CurrentPath.includes(childrenItem?.title?.toLowerCase()) ? "active" : ""}`}
                            // className={`${childrenItem.active ? 'active' : ''}`} bonusui
                            onClick={() => toggletNavActive(childrenItem)}>
                            {t(childrenItem.title)}
                          </Link>
                        ) : (
                          ""
                        )}

                        {childrenItem.children ? (
                          <ul className="nav-sub-childmenu submenu-content" style={CurrentPath.includes(childrenItem?.title?.toLowerCase()) || childrenItem.active ? { display: "block" } : { display: "none" }}>
                            {childrenItem.children.map((childrenSubItem, key) => (
                              <li key={key}>
                                {childrenSubItem.type === "link" ? (
                                  <Link
                                    to={childrenSubItem.path}
                                    className={`${CurrentPath.includes(childrenSubItem?.title?.toLowerCase()) ? "active" : ""}`}
                                    // className={`${childrenSubItem.active ? 'active' : ''}`}
                                    onClick={() => toggletNavActive(childrenSubItem)}>
                                    {t(childrenSubItem.title)}
                                  </Link>
                                ) : (
                                  ""
                                )}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          ""
                        )}
                      </li>
                    );
                  })}
                </ul>
              ) : (
                ""
              )}
            </li>
          ))}
        </Fragment>
      ))}
    </>
  );
};

export default SidebarMenuItems;
