import React, { useState } from 'react';
import { Card, CardBody, CardHeader, Row, Col, Nav, NavItem, NavLink, TabContent, TabPane } from 'reactstrap';
import { H5, P } from '../../../../../AbstractElements';
import { Hometxt, Inbox, MaterialRightTab, Profile, Settings } from '../../../../../Constant';

const RightTab = () => {
  const [RightLineTab, setRightLineTab] = useState('1');
  return (
    <Col sm='12' xl='6' className='xl-100'>
      <Card>
        <CardHeader>
          <H5>{MaterialRightTab}</H5>
          <span>
            {'Add'} <code>{'.border-tab nav-right'}</code> {'class with nav class'}
          </span>
        </CardHeader>
        <CardBody>
          <Row>
            <Col sm='9'>
              <TabContent activeTab={RightLineTab} className='text-end'>
                <TabPane className='fade show' tabId='1'>
                  <P>
                    {
                      'Skull print sporty trendy t-shirt polo polished finishing touches cardigans tunics metallic jumper. Slimming removable contrast straps black waist band ultra-feminine floral print versatility of wear sun-soaked. Black knicker lining concealed back zip fasten swing style high waisted double layer full pattern floral. Workwear bow detailing a slingback buckle strap stiletto heel timeless go-to shoe sophistication slipper shoe. Embroidered logo chest pocket locker loop button-flap breast pockets fastening jetted.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='2'>
                  <P>
                    {
                      'Trendy t-shirt polo polished finishing touches cardigans tunics metallic jumper. Slimming removable contrast straps black waist band ultra-feminine floral print versatility of wear sun-soaked. Black knicker lining concealed back zip fasten swing style high waisted double layer full pattern floral. Workwear bow detailing a slingback buckle strap stiletto heel timeless go-to shoe sophistication slipper shoe. Embroidered logo chest pocket locker loop button-flap breast pockets fastening jetted.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='3'>
                  <P>
                    {
                      'Slimming removable contrast straps black waist band ultra-feminine floral print versatility of wear sun-soaked. Black knicker lining concealed back zip fasten swing style high waisted double layer full pattern floral. Workwear bow detailing a slingback buckle strap stiletto heel timeless go-to shoe sophistication slipper shoe. Embroidered logo chest pocket locker loop button-flap breast pockets fastening jetted.'
                    }
                  </P>
                </TabPane>
                <TabPane tabId='4'>
                  <P>
                    {
                      'Black waist band ultra-feminine floral print versatility of wear sun-soaked. Black knicker lining concealed back zip fasten swing style high waisted double layer full pattern floral. Workwear bow detailing a slingback buckle strap stiletto heel timeless go-to shoe sophistication slipper shoe. Embroidered logo chest pocket locker loop button-flap breast pockets fastening jetted.'
                    }
                  </P>
                </TabPane>
              </TabContent>
            </Col>
            <Col sm='3' className='tabs-responsive-side'>
              <Nav className='flex-column border-tab nav-right'>
                <NavItem>
                  <NavLink href='#javascript' className={RightLineTab === '1' ? 'active' : ''} onClick={() => setRightLineTab('1')}>
                    {Hometxt}
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink href='#javascript' className={RightLineTab === '2' ? 'active' : ''} onClick={() => setRightLineTab('2')}>
                    {Profile}
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink href='#javascript' className={RightLineTab === '3' ? 'active' : ''} onClick={() => setRightLineTab('3')}>
                    {Inbox}
                  </NavLink>
                </NavItem>
                <NavItem>
                  <NavLink href='#javascript' className={RightLineTab === '4' ? 'active' : ''} onClick={() => setRightLineTab('4')}>
                    {Settings}
                  </NavLink>
                </NavItem>
              </Nav>
            </Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default RightTab;
