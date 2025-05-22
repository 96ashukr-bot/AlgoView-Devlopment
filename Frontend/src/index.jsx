import React from "react";
import { useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./index.scss";
import App from "./App";
import "./i18n";
import reportWebVitals from "./reportWebVitals";
import { LogoProvider } from "./Components/UiKits/Logo/LogoContext";

const Root = () => {

  useEffect(() => {
    const storedFavicon = localStorage.getItem('companyFavicon');
    if (storedFavicon) {
      updateFavicon(storedFavicon);
    }
  }, []);

  const updateFavicon = (faviconUrl) => {
    const existingFavicons = document.querySelectorAll("link[rel~='icon']");
    existingFavicons.forEach(link => link.parentNode.removeChild(link));
  
    if (faviconUrl) {
      const newLink = document.createElement('link');
      newLink.rel = 'icon';
      newLink.href = faviconUrl;
      document.head.appendChild(newLink);
    }
  };

  return (
    <LogoProvider>
      <div className="App">
        <App />
      </div>
    </LogoProvider>

  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<Root />);

// ReactDOM.createRoot(<App />, document.getElementById("root"));

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
