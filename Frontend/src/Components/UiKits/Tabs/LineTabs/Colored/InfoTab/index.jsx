import React, { useState } from 'react';
import { Card, CardBody, CardHeader, Col, Nav, NavLink, Row, TabContent, TabPane } from 'reactstrap';
import { H5, P } from '../../../../../../AbstractElements';
import { Hometxt, Inbox, Profile, Settings, SimpleMaterialTab } from '../../../../../../Constant';

const InfoColorTab = () => {
  const [InfoRightLineTab, setInfoRightLineTab] = useState('1');
  return (
    <Col sm='12' xl='6' className='xl-100'>
      <Card>
        <CardHeader>
          <H5>{SimpleMaterialTab}</H5>
          <span>
            {'Add'} <code>{'nav-info'}</code> {'class with nav class'}
          </span>
        </CardHeader>
        <CardBody>
          <Row>
            <Col sm='9' className='tabs-responsive-side'>
              <TabContent activeTab={InfoRightLineTab}>
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
            <Col sm='3'>
              <Nav className='flex-column nav-info border-tab nav-right'>
                <NavLink href='#javascript' className={InfoRightLineTab === '1' ? 'active' : ''} onClick={() => setInfoRightLineTab('1')}>
                  {Hometxt}
                </NavLink>
                <NavLink href='#javascript' className={InfoRightLineTab === '2' ? 'active' : ''} onClick={() => setInfoRightLineTab('2')}>
                  {Profile}
                </NavLink>
                <NavLink href='#javascript' className={InfoRightLineTab === '3' ? 'active' : ''} onClick={() => setInfoRightLineTab('3')}>
                  {Inbox}
                </NavLink>
                <NavLink href='#javascript' className={InfoRightLineTab === '4' ? 'active' : ''} onClick={() => setInfoRightLineTab('4')}>
                  {Settings}
                </NavLink>
              </Nav>
            </Col>
          </Row>
        </CardBody>
      </Card>
    </Col>
  );
};

export default InfoColorTab;
