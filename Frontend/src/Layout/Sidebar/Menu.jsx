export const MENUITEMS = [
  {
    menutitle: "General",
    menucontent: "Dashboards,Widgets",
    Items: [
      { path: `/dashboard/algoviewtech/admin`, icon: "home", title: "Dashboard", type: "link" },
 
      {
        title: "Sub Admin",
        icon: "user",
        // path: `/app/users/profile`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/subadmin/userlist`, title: "All Sub Admin", type: "link" },
          { path: `/subadmin/inactive-list`, title: "In Active Clients", type: "link" },
          { path: `/subadmin/active-list`, title: "Active Clients", type: "link" },
        ],
      },

      // {
      //   title: "Roles & Permissions",
      //   icon: "blog",
      //   // path: `/app/users/profile`,
      //   type: "sub",
      //   bookmark: true,
      //   active: false,
      //   children: [
      //     { path: `/dashboard/rolepermmision`, title: "Role List", type: "link" },
      //     { path: `/dashboard/rolepermmisionupdate`, title: "Role User Manager", type: "link" },
      //   ],
      // },
      
      {
        title: "Kyc",
        icon: "charts",
        // path: `/app/users/profile`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/kyc/kyclist`, title: "Kyc List", type: "link" },
        ],
      },
      {
        title: "Client",
        icon: "user",
        // path: `/table/datatable/addclient`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/client/addclient`, title: "Add Client", type: "link" },
          { path: `/client/all-clients-list`, title: "Client List", type: "link" },
          { path: `/client/expiredclients`, title: "Expired Client", type: "link" },
        ],
      },

      {
        title: "Trade Details",
        icon: "project",
        // path: `/table/datatable/signals`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/tradedetails/signals`, title: "Signals", type: "link" },
          { path: `/tradedetails/trade-history`, title: "Trade History", type: "link" },
          { path: `/tradedetails/complete-trade-history`, title: "Complete Trade", type: "link" },
          { path: `/tradedetails/trade-view`, title: "Client Trade", type: "link" },
          { path: `/tradedetails/trading-status`, title: "Trading Status", type: "link" },
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
          { path: `/service-manage/all-service-list`, title: "All Service", type: "link" },
          { path: `/service-manage/group-services-list`, title: "Group Service", type: "link" },
          { path: `/service-manage/strategies`, title: "Strategies", type: "link" },          
        ],
      },

      {
        title: "License",
        icon: "chat",
        // path: `/table/datatable/signals`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/license/transactionlicense`, title: "Transaction License", type: "link" },
          { path: `/license/expiredlicense`, title: "Expired License", type: "link" },
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
        title: "Settings",
        icon: "learning",
        // path: `/table/datatable/signals`,
        type: "sub",
        bookmark: true,
        active: false,
        children: [
          { path: `/settings/category`, title: "Category", type: "link" },
          { path: `/settings/segment`, title: "Segment", type: "link" },
          { path: `/settings/services`, title: "Services", type: "link" },
          // { path: `/settings/license`, title: "License", type: "link" },
          { path: `/settings/brokers`, title: "Brokers", type: "link" },
          { path: `/settings/companydetails`, title: "Company Details", type: "link" },
          { path: `/settings/emailaccount`, title: "Email Account", type: "link" },
          { path: `/settings/websocket`, title: "Web Socket", type: "link" },                                
        ],
      },

    ],
  },

  // {
  //   menutitle: "",
  //   menucontent: "Ready to use Apps",
  //   Items: [
  //     {
  //       title: "Project",
  //       icon: "project",
  //       type: "sub",
  //       badge: "badge badge-light-secondary",
  //       badgetxt: "New",
  //       active: false,
  //       children: [
  //         { path: `/app/project/project-list`, type: "link", title: "Project-List" },
  //         { path: `/app/project/new-project`, type: "link", title: "Create New" },
  //       ],
  //     },
  //     { path: `/app/file-manager`, icon: "file", title: "File-Manager", type: "link" },
  //     {
  //       title: "Ecommerce",
  //       icon: "ecommerce",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/app/ecommerce/product`, title: "Products", type: "link" },
  //         { path: `/app/ecommerce/product-page/1`, title: "Product-Page", type: "link" },
  //         { path: `/app/ecommerce/product-list`, title: "Product-List", type: "link" },
  //         { path: `/app/ecommerce/payment-details`, title: "Payment-Detail", type: "link" },
  //         { path: `/app/ecommerce/orderhistory`, title: "OrderHistory", type: "link" },
  //         { path: `/app/ecommerce/invoice`, title: "Invoice", type: "link" },
  //         { path: `/app/ecommerce/cart`, title: "Cart", type: "link" },
  //         { path: `/app/ecommerce/wishlist`, title: "Wishlist", type: "link" },
  //         { path: `/app/ecommerce/checkout`, title: "checkout", type: "link" },
  //         { path: `/app/ecommerce/pricing`, title: "Pricing", type: "link" },
  //       ],
  //     },
  //     { path: `/app/email-app`, icon: "email", title: "Email", type: "link" },
  //     {
  //       title: "Chat",
  //       icon: "chat",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/app/chat-app/chats`, type: "link", title: "Chats" },
  //         { path: `/app/chat-app/chat-video-app`, type: "link", title: "Video-app" },
  //       ],
  //     },
      // {
      //   title: "Users",
      //   icon: "user",
      //   path: `/app/users/profile`,
      //   type: "sub",
      //   bookmark: true,
      //   active: false,
      //   children: [
      //     { path: `/app/users/profile`, type: "link", title: "User Profile" },
      //     { path: `/app/users/edit`, type: "link", title: "User Edit" },
      //     { path: `/app/users/cards`, type: "link", title: "User Cards" },
      //   ],
      // },
  //     { path: `/app/bookmark`, icon: "bookmark", type: "link", title: "Bookmark" },
  //     {
  //       title: "Contact",
  //       icon: "contact",
  //       type: "link",
  //       active: false,
  //       path: `/app/contact-app/contacts`,
  //     },
  //     { path: `/app/task`, icon: "task", type: "link", title: "Task" },
  //     { path: `/app/calendar/draggable-calendar`, icon: "calendar", type: "link", title: "Calendar" },

  //     { path: `/app/social-app`, icon: "social", type: "link", title: "Social-App", bookmark: true },
  //     { path: `/app/todo-app/todo`, icon: "to-do", type: "link", title: "Todo" },
  //     { path: `/app/search`, icon: "search", type: "link", title: "Search Result" },
  //   ],
  // },

  // {
  //   menutitle: "Forms & Table",
  //   menucontent: "Ready to use froms & tables",
  //   Items: [
  //     {
  //       title: "Forms",
  //       icon: "form",
  //       type: "sub",
  //       menutitle: "Forms & Table",
  //       menucontent: "Ready to use froms & tables",
  //       active: false,
  //       children: [
  //         {
  //           title: "Controls",
  //           type: "sub",
  //           children: [
  //             { title: "Validation", type: "link", path: `/forms/controls/validation` },
  //             { title: "Input", type: "link", path: `/forms/controls/input` },
  //             { title: "Radio-Checkbox", type: "link", path: `/forms/controls/radio-checkbox` },
  //             { title: "Group", type: "link", path: `/forms/controls/group` },
  //             { title: "MegaOption", type: "link", path: `/forms/controls/megaoption` },
  //           ],
  //         },
  //         {
  //           title: "Widget",
  //           type: "sub",
  //           children: [
  //             { title: "Datepicker", type: "link", path: `/forms/widget/datepicker` },
  //             { title: "Datetimepicker", type: "link", path: `/forms/widget/datetimepicker` },
  //             { title: "Touchspin", type: "link", path: `/forms/widget/touchspin` },
  //             { title: "Select2", type: "link", path: `/forms/widget/select2` },
  //             { title: "Switch", type: "link", path: `/forms/widget/switch` },
  //             { title: "Typeahead", type: "link", path: `/forms/widget/typeahead` },
  //             { title: "Clipboard", type: "link", path: `/forms/widget/clipboard` },
  //           ],
  //         },
  //         {
  //           title: "Layout",
  //           type: "sub",
  //           children: [
  //             { path: `/forms/layout/formdefault`, title: "FormDefault", type: "link" },
  //             { path: `/forms/layout/formwizard`, title: "FormWizard", type: "link" },
  //           ],
  //         },
  //       ],
  //     },

  //     {
  //       title: "Table",
  //       icon: "table",
  //       type: "sub",
  //       children: [
  //         {
  //           title: "ReactstrapTable",
  //           type: "link",
  //           path: `/table/reactstraptable/basictable`,
  //         },
  //         {
  //           title: "DataTable",
  //           path: `/table/datatable`,
  //           type: "link",
  //         },
  //       ],
  //     },
  //   ],
  // },

  // {
  //   menutitle: "Components",
  //   menucontent: "UI Components & Elements",
  //   Items: [
  //     {
  //       title: "Ui-Kits",
  //       icon: "ui-kits",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/ui-kits/typography`, title: "Typography", type: "link" },
  //         { path: `/ui-kits/avatar`, title: "Avatar", type: "link" },
  //         { path: `/ui-kits/helper-class`, title: "Helper-Class", type: "link" },
  //         { path: `/ui-kits/grids`, title: "Grids", type: "link" },
  //         { path: `/ui-kits/tag-pills`, title: "Tag-Pills", type: "link" },
  //         { path: `/ui-kits/progress`, title: "Progress", type: "link" },
  //         { path: `/ui-kits/modal`, title: "Modal", type: "link" },
  //         { path: `/ui-kits/alert`, title: "Alert", type: "link" },
  //         { path: `/ui-kits/popover`, title: "Popover", type: "link" },
  //         { path: `/ui-kits/tooltips`, title: "Tooltips", type: "link" },
  //         { path: `/ui-kits/spinner`, title: "Spinner", type: "link" },
  //         { path: `/ui-kits/dropdown`, title: "Dropdown", type: "link" },
  //         { path: `/ui-kits/accordion`, title: "Accordion", type: "link" },
  //         {
  //           title: "Tabs",
  //           type: "sub",
  //           children: [
  //             { title: "Bootstrap", type: "link", path: `/ui-kits/tabs/bootstrap` },
  //             { title: "Line", type: "link", path: `/ui-kits/tabs/line` },
  //           ],
  //         },
  //         { path: `/ui-kits/shadow`, title: "Shadow", type: "link" },
  //         { path: `/ui-kits/list`, title: "List", type: "link" },
  //       ],
  //     },

  //     {
  //       title: "Bonus-Ui",
  //       icon: "bonus-kit",
  //       type: "sub",
  //       badge1: true,
  //       active: false,
  //       children: [
  //         { path: `/bonus-ui/scrollable`, title: "Scrollable", type: "link" },
  //         { path: `/bonus-ui/bootstrap-notify`, title: "Bootstrap-Notify", type: "link" },
  //         { path: `/bonus-ui/tree-view`, title: "Tree View", type: "link" },
  //         { path: `/bonus-ui/rating`, title: "Rating", type: "link" },
  //         { path: `/bonus-ui/dropzone`, title: "Dropzone", type: "link" },
  //         { path: `/bonus-ui/tour`, title: "Tour ", type: "link" },
  //         { path: `/bonus-ui/sweet-alert`, title: "Sweet-Alert", type: "link" },
  //         { path: `/bonus-ui/carousel`, title: "Carousel", type: "link" },
  //         { path: `/bonus-ui/ribbons`, title: "Ribbons", type: "link" },
  //         { path: `/bonus-ui/pagination`, title: "Pagination", type: "link" },
  //         { path: `/bonus-ui/breadcrumb`, title: "Breadcrumb", type: "link" },
  //         { path: `/bonus-ui/rangeslider`, title: "RangeSlider", type: "link" },
  //         { path: `/bonus-ui/imagecropper`, title: "ImageCropper", type: "link" },
  //         { path: `/bonus-ui/stickynotes`, title: "StickyNotes", type: "link" },
  //         { path: `/bonus-ui/drag_and_drop`, title: "Drag_and_Drop", type: "link" },
  //         { path: `/bonus-ui/image-upload`, title: "Image-Upload", type: "link" },
  //         { path: `/bonus-ui/card/basiccards`, title: "BasicCards", type: "link" },
  //         { path: `/bonus-ui/card/creativecards`, title: "CreativeCards", type: "link" },
  //         { path: `/bonus-ui/card/tabcard`, title: "TabCard", type: "link" },
  //         { path: `/bonus-ui/timelines/timeline1`, title: "Timeline1", type: "link" },
  //       ],
  //     },

  //     {
  //       title: "Icons",
  //       icon: "icons",
  //       path: `/icons/flag_icons`,
  //       type: "sub",
  //       active: false,
  //       bookmark: true,
  //       children: [
  //         { path: `/icons/flag_icons`, title: "Flag Icon", type: "link" },
  //         { path: `/icons/fontawesome_icon`, title: "Fontawesome Icon", type: "link" },
  //         { path: `/icons/ico_icon`, title: "Ico Icon", type: "link" },
  //         { path: `/icons/themify_icons`, title: "Themify Icon", type: "link" },
  //         { path: `/icons/feather_icons`, title: "Feather Icon", type: "link" },
  //         { path: `/icons/weather_icons`, title: "Weather Icons", type: "link" },
  //       ],
  //     },

  //     {
  //       title: "Buttons",
  //       icon: "button",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/buttons/simplebutton`, title: "SimpleButton", type: "link" },
  //         { path: `/buttons/flat`, title: "Flat", type: "link" },
  //         { path: `/buttons/edge`, title: "Edge", type: "link" },
  //         { path: `/buttons/raised`, title: "Raised", type: "link" },
  //         { path: `/buttons/group`, title: "Group", type: "link" },
  //       ],
  //     },

  //     {
  //       title: "Charts",
  //       icon: "charts",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/charts/apex`, type: "link", title: "Apex" },
  //         { path: `/charts/google`, type: "link", title: "Google" },
  //         { path: `/charts/chartjs`, type: "link", title: "Chartjs" },
  //       ],
  //     },
  //   ],
  // },

  // {
  //   menutitle: "Pages",
  //   menucontent: "All neccesory pages added",
  //   Items: [
  //     {
  //       icon: "sample-page",
  //       badge2: true,
  //       active: false,
  //       path: `/pages/sample-page`,
  //       title: "Sample-Page",
  //       type: "link",
  //     },
  //     {
  //       title: "Others",
  //       icon: "others",
  //       type: "sub",
  //       children: [
  //         {
  //           title: "Error Pages",
  //           type: "sub",
  //           children: [
  //             { title: "Error Page 1", type: "link", path: `/pages/errors/error400` },
  //             { title: "Error Page 2", type: "link", path: `/pages/errors/error401` },
  //             { title: "Error Page 3", type: "link", path: `/pages/errors/error403` },
  //             { title: "Error Page 4", type: "link", path: `/pages/errors/error404` },
  //             { title: "Error Page 5", type: "link", path: `/pages/errors/error500` },
  //             { title: "Error Page 6", type: "link", path: `/pages/errors/error503` },
  //           ],
  //         },
  //         {
  //           title: "Authentication",
  //           type: "sub",
  //           children: [
  //             { title: "Login Simple", type: "link", path: `/pages/authentication/login-simple/register-simple/:layout` },
  //             { title: "Login with bg image", type: "link", path: `/pages/authentication/login-bg-img` },
  //             { title: "Login with image two", type: "link", path: `/pages/authentication/login-img` },
  //             { title: "Login with validation", type: "link", path: `/pages/authentication/login-validation` },
  //             { title: "Login with tooltip", type: "link", path: `/pages/authentication/login-tooltip` },
  //             { title: "Login with sweetalert", type: "link", path: `/pages/authentication/login-sweetalert` },
  //             { title: "Register Simple", type: "link", path: `/pages/authentication/register-simple/:layout` },
  //             { title: "Register with Bg Image", type: "link", path: `/pages/authentication/register-bg-img` },
  //             { title: "Register with Bg Video", type: "link", path: `/pages/authentication/register-video` },
  //             { title: "Unloack User", type: "link", path: `/pages/authentication/unlock-user` },
  //             { title: "Forget Password", type: "link", path: `/pages/authentication/forget-pwd/:layout` },
  //             { title: "Reset Password", type: "link", path: `/pages/authentication/create-pwd` },
  //             { title: "Maintenance", type: "link", path: `/pages/authentication/maintenance` },
  //           ],
  //         },
  //         {
  //           title: "Coming Soon",
  //           type: "sub",
  //           children: [
  //             { title: "Coming Simple", type: "link", path: `/pages/comingsoon/comingsoon` },
  //             { title: "Coming with Bg Video", type: "link", path: `/pages/comingsoon/coming-bg-video` },
  //             { title: "Coming with bg Image", type: "link", path: `/pages/comingsoon/coming-bg-img` },
  //           ],
  //         },
  //       ],
  //     },
  //   ],
  // },

  // {
  //   menutitle: "Miscellaneous",
  //   menucontent: "Bouns Pages & Apps",
  //   Items: [
  //     {
  //       title: "Gallery",
  //       icon: "gallery",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/app/gallery/grids`, title: "Grids", type: "link" },
  //         { path: `/app/gallery/griddesc`, title: "GridDesc", type: "link" },
  //         { path: `/app/gallery/masonrys`, title: "Masonrys", type: "link" },
  //         { path: `/app/gallery/masonrydesc`, title: "MasonryDesc", type: "link" },
  //         { path: `/app/gallery/hover_effect`, title: "Hover_Effect", type: "link" },
  //       ],
  //     },

  //     {
  //       title: "Blog",
  //       icon: "blog",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/app/blog/blogdetails`, title: "BlogDetails", type: "link" },
  //         { path: `/app/blog/blogsingle`, title: "BlogSingle", type: "link" },
  //         { path: `/app/blog/blogpost`, title: "BlogPost", type: "link" },
  //       ],
  //     },
  //     { path: `/app/faq`, icon: "faq", type: "link", active: false, title: "FAQ" },
  //     {
  //       title: "JobSearch",
  //       icon: "job-search",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/app/jobsearch/cardview`, title: "CardView", type: "link" },
  //         { path: `/app/jobsearch/joblist`, title: "JobList", type: "link" },
  //         { path: `/app/jobsearch/jobdetail`, title: "JobDetail", type: "link" },
  //         { path: `/app/jobsearch/jobapply`, title: "JobApply", type: "link" },
  //       ],
  //     },
  //     {
  //       title: "Learning",
  //       icon: "learning",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/app/learning/learninglist`, title: "LearningList", type: "link" },
  //         { path: `/app/learning/learningdetail`, title: "LearningDetail", type: "link" },
  //       ],
  //     },
  //     {
  //       title: "Map",
  //       icon: "maps",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/app/map/googlemap`, type: "link", title: "GoogleMap" },
  //         { path: `/app/map/pigeonmap`, type: "link", title: "PigeonMap" },
  //       ],
  //     },
  //     {
  //       title: "Editor",
  //       icon: "editors",
  //       type: "sub",
  //       active: false,
  //       children: [
  //         { path: `/editor/ckeditor`, type: "link", title: "CKEditor" },
  //         { path: `/editor/mdeeditor`, type: "link", title: "MDEEditor" },
  //         { path: `/editor/aceeditor`, type: "link", title: "ACEEditor" },
  //       ],
  //     },

  //     { path: `/app/knowledgebase`, icon: "knowledgebase", type: "link", active: false, title: "Knowledgebase" },
  //     { path: `/app/supportticket`, icon: "support-tickets", type: "link", active: false, title: "SupportTicket" },
  //   ],
  // },
  
];
