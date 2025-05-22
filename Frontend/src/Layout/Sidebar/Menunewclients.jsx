export const MENUITEMSNEW = [
  {
    menutitle: "General",
    menucontent: "Dashboards,Widgets",
    Items: [
      { path: `/dashboard/algoviewtech/user`, icon: "home", title: "Dashboard", type: "link" },
      {
        title: "Trade Details",
        icon: "project",
        // path: `/table/datatable/signals`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/tradedetails/signals`, title: "Signals", type: "link" },
          { path: `/tradedetails/client-trade-history`, title: "Trade History", type: "link" },
          { path: `/tradedetails/complete-trade-history`, title: "Complete Trade", type: "link" },
          { path: `/tradedetails/trade-view`, title: "Client Trade", type: "link" },
        ],
      },

      {
        title: "Service Management",
        icon: "others",
        // path: `/table/datatable/signals`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          // { path: `/service-manage/all-service-list`, title: "All Service", type: "link" },
          // { path: `/service-manage/group-services-list`, title: "Group Service", type: "link" },
          { path: `/service-manage/clientstrategies`, title: "Strategies", type: "link" },          
        ],
      },
     
      {
        title: "API Info",
        icon: "editors",
        // path: `/table/datatable/signals`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/apiinfo/apikeys`, title: "API Keys", type: "link" },
        ],
      },

      {
        title: "Help Center",
        icon: "ui-kits",
        // path: `/table/datatable/signals`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/dashboard/helpcenter`, title: "Help Center", type: "link" },
        ],
      },

    ],
  },
    
];
