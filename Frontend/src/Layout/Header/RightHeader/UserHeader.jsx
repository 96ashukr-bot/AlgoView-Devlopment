import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogIn, User } from "react-feather";
import man from "../../../assets/images/dashboard/defaultpicture.jpg";
import { LI, UL, Image, P } from "../../../AbstractElements";
import CustomizerContext from "../../../_helper/Customizer";
import { baseUrl } from "../../../ConfigUrl/config";
import { Account, KycUpdate } from "../../../Constant";
import { fetchUserProfile, logoutUser } from "../../../Services/Authentication";
import './RightHeader.css'

const UserHeader = () => {
  const history = useNavigate();
  const [profile, setProfile] = useState(man);
  const [name, setName] = useState("Loading...");
  const [role, setRole] = useState("");
  const { layoutURL } = useContext(CustomizerContext);
  const authenticated = JSON.parse(localStorage.getItem("authenticated"));
  const [dropdownOpen, setDropdownOpen] = useState(false);
  
  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      const data = await fetchUserProfile();
      if (data) {
        const firstName = data.firstName || "No";
        const lastName = data.lastName || "Name";
        setName(`${firstName} ${lastName}`);

        if (data.profilePicture) {
          const profilePictureUrl = `${baseUrl}${data.profilePicture}`;
          setProfile(profilePictureUrl);
        }
        
        if (data.role && data.role.name) {
          setRole(data.role.name); 
        }
      }
    } catch (error) {
      console.error("Error fetching user profile:", error);
    }
  };

  const Logout = async () => {
    try {
      await logoutUser();
      localStorage.removeItem('hasShownInitialAlert');
      history(`/login`);
    } catch (error) {
      console.error("Logout failed:", error.message);
    }
  };

  const UserMenuRedirect = (redirect) => {
    history(redirect);
  };

  const toggleDropdown = () => {
    setDropdownOpen(!dropdownOpen); 
  };

  const closeDropdown = () => {
    setDropdownOpen(false);
  };

  return (
    <li className="profile-nav pe-0 py-0">
      <div className="media profile-media" onClick={toggleDropdown}>
        <Image
          attrImage={{
            className: "b-r-10 m-0",
            src: profile || man,
            alt: "",
            style: { width: "35px", height: "35px" },
          }}
        />
        <div className="media-body">
          <span>{name}</span>
          <P attrPara={{ className: "mb-0 font-roboto" }}>
            {role} <i className={`middle fa fa-angle-${dropdownOpen ? "up" : "down"}`}></i>
          </P>
        </div>
      </div>

      {dropdownOpen && (
        <UL attrUL={{ className: "simple-list profile-dropdown" }}>
          <LI
            attrLI={{
              onClick: () => {
                UserMenuRedirect(`/algoview/users/profile`);
                closeDropdown(); 
              },
            }}
          >
            <User />
            <span>{Account}</span>
          </LI>

          {role.toLowerCase() === "client" && (
            <LI
              attrLI={{
                onClick: () => {
                  UserMenuRedirect(`/algoview/kyc-update`);
                  closeDropdown();
                },
              }}
            >
              <User />
              <span>{KycUpdate}</span>
            </LI>
          )}

          <LI
            attrLI={{
              onClick: () => {
                Logout();
                closeDropdown();
              },
            }}
          >
            <LogIn />
            <span>Log Out</span>
          </LI>
        </UL>
      )}
    </li>
  );
};

export default UserHeader;
