import React, { Fragment, useContext, useState } from 'react';
import { Container, Row, Col, Card, CardBody, Nav, NavItem, NavLink, TabContent, TabPane } from 'reactstrap';
import { Target, Info, CheckCircle, PlusCircle } from 'react-feather';
import { Link } from 'react-router-dom';
import { Done, All, Doing, CreateNewProject } from '../../../../Constant';
import { Breadcrumbs } from '../../../../AbstractElements';
import ProjectContext from '../../../../_helper/Project';
import CusClass from '../Common/CusClass';
import CustomizerContext from '../../../../_helper/Customizer';

const Project = () => {
  const { layoutURL } = useContext(CustomizerContext);
  const [activeTab, setActiveTab] = useState('1');
  const { allData } = useContext(ProjectContext);

  return (
    <Fragment>
      <Breadcrumbs parent="Project" title="Project List" mainTitle="Project List" />
      <Container fluid={true}>
        <Row className="project-card">
          <Col md="12" className="project-list">
            <Card>
              <Row>
                <Col md="6">
                  <Nav tabs className="border-tab">
                    <NavItem><NavLink className={activeTab === '1' ? 'active' : ''} onClick={() => setActiveTab('1')}><Target />{All}</NavLink></NavItem>
                    <NavItem><NavLink className={activeTab === '2' ? 'active' : ''} onClick={() => setActiveTab('2')}><Info />{Doing}</NavLink></NavItem>
                    <NavItem><NavLink className={activeTab === '3' ? 'active' : ''} onClick={() => setActiveTab('3')}><CheckCircle />{Done}</NavLink></NavItem>
                  </Nav>
                </Col>
                <Col md="6">
                  <div className="text-end">
                    <Link className="btn btn-primary" style={{ color: 'white' }} to={`/app/project/new-project/${layoutURL}`}> <PlusCircle />{CreateNewProject}</Link>
                  </div>
                </Col>
              </Row>
            </Card>
          </Col>
          <Col sm="12">
            <Card>
              <CardBody>
                <TabContent activeTab={activeTab}>
                  <TabPane tabId="1">
                    <Row>
                      {allData.map((item, i) =>
                        <CusClass item={item} key={i} />
                      )}
                    </Row>
                  </TabPane>
                  <TabPane tabId="2">
                    <Row>
                      {allData.map((item, i) =>
                      (item.badge === 'Doing' ?
                        <CusClass item={item} key={i} />
                        : '')
                      )}
                    </Row>
                  </TabPane>
                  <TabPane tabId="3">
                    <Row>
                      {allData.map((item, i) =>
                      (item.badge === 'Done' ?
                        <CusClass item={item} key={i} />
                        : '')
                      )}
                    </Row>
                  </TabPane>
                </TabContent>
              </CardBody>
            </Card>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
};

export default Project;