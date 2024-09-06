import { useEffect } from "react";
import UserDetails from "../../Application/Users/UsersProfile/UserDetail";
import UserDetails2 from "../../Application/Users/UsersProfile/UserDetail2";
import UserDetails4 from "../../Application/Users/UsersProfile/UserDetail4";
import UserDetails3 from "../../Application/Users/UsersProfile/UserDetails3";
import UserProfile from "./UserProfile";
import { useTour } from "@reactour/tour";
import { Breadcrumbs } from "../../../AbstractElements";
import { Container, Row } from "reactstrap";

const TourMain = () => {
  const { setIsOpen } = useTour();
  useEffect(() => {
    var timer = setTimeout(() => {
      setIsOpen(true);
    }, 100);
    return () => {
      clearTimeout(timer);
    };
  }, []);
  return (
    <>
      <Breadcrumbs mainTitle="Tour" parent="Bouns Ui" title="Tour" />

      <Container fluid={true}>
        <div className="user-profile">
          <Row>
            <UserProfile />
            <UserDetails />
            <UserDetails2 />
            <UserDetails3 />
            <UserDetails4 />
          </Row>
        </div>
      </Container>
    </>
  );
};

export default TourMain;
