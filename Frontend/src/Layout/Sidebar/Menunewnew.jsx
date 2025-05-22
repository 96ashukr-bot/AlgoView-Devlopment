export const MENUITEMSNEWNEW = [
  {
    menutitle: "General",
    menucontent: "Dashboards,Widgets",
    Items: [
      { path: `/dashboard/algoviewtech/admin`, icon: "home", title: "Dashboard", type: "link" },
      {
        title: "Client",
        icon: "user",
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/client/addclient`, title: "Add Client", type: "link" },
          { path: `/client/all-clients-list`, title: "Client List", type: "link" },
        ],
      },

      {
        title: "Trade Details",
        icon: "project",
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/tradedetails/signals`, title: "Signals", type: "link" },
          { path: `/tradedetails/trade-history`, title: "Trade History", type: "link" },
          { path: `/tradedetails/complete-trade-history`, title: "Complete Trade", type: "link" },
          { path: `/tradedetails/trade-view`, title: "Client Trade", type: "link" },
        ],
      },
      {
        title: "License",
        icon: "chat",
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/license/license-payment-list`, title: "License Payment", type: "link" },
          { path: `/license/transactionlicense`, title: "Transaction License", type: "link" },
          { path: `/license/expiredlicense`, title: "Expired License", type: "link" },
        ],
      },
      {
        title: "API Info",
        icon: "editors",
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
