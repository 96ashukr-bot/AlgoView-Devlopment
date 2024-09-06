import React, { Fragment, useState } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import NavClass from './NavClass';
import TabClass from './TabClass';

const Task = () => {
  const newtaskdata = '';
  const [activeTab, setActiveTab] = useState('1');

  const activeToggle = ((tab) => {
    setActiveTab(tab);
  });

  return (
    <Fragment>
      <Breadcrumbs mainTitle="Tasks" parent="Apps" title="Tasks" />
      <Container fluid={true}>
        <div className="email-wrap bookmark-wrap">
          <Row>
            <NavClass newtaskdata={newtaskdata} activeToggle={activeToggle} />
            <TabClass activeTab={activeTab} />
          </Row>
        </div>
      </Container>
    </Fragment>
  );
};

export default Task;