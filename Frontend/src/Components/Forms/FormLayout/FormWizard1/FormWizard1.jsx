import React, { Fragment, useState } from "react";
import Registration from "./Registration";
import Email from "./Email";
import Birthdate from "./Birthdate";
import { Container, Row, Col, Card, CardBody } from "reactstrap";
import { FormWizardWithIcon } from "../../../../Constant";
import { Breadcrumbs } from "../../../../AbstractElements";
import HeaderCard from "../../../Common/Component/HeaderCard";

const FormWizard = () => {
  const [steps, setSteps] = useState(1);
  const [formdata, setFormdata] = useState({});

  return (
    <Fragment>
      <Breadcrumbs parent="Forms" mainTitle="Form Wizard" subParent="Form Layout" title="Form Wizard" />
      <Container fluid={true}>
        <Row>
          <Col sm="12">
            <Card>
              <HeaderCard title={FormWizardWithIcon} />
              <CardBody>
                {steps === 1 && <Registration setSteps={setSteps} setFormdata={setFormdata} formdata={formdata} />}

                {steps === 2 && <Email setSteps={setSteps} setFormdata={setFormdata} formdata={formdata} />}

                {steps === 3 && <Birthdate setSteps={setSteps} setFormdata={setFormdata} formdata={formdata} />}

                <div className="text-center">
                  <span className={`step ${steps > 1 ? "finish" : ""} ${steps === 1 ? "active" : ""}`} />
                  <span className={`step ${steps > 2 ? "finish" : ""} ${steps === 2 ? "active" : ""}`} />
                  <span className={`step ${steps > 3 ? "finish" : ""} ${steps === 3 ? "active" : ""}`} />
                </div>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default FormWizard;
