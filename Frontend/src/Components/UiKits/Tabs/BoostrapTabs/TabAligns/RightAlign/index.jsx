import React, { useState } from 'react';
import { Card, CardBody, Col, Nav, NavItem, NavLink, TabContent, TabPane } from 'reactstrap';
import { Contact, Hometxt, Profile, TabsRightAlign } from '../../../../../../Constant';
import { P } from '../../../../../../AbstractElements';
import HeaderCard from '../../../../../Common/Component/HeaderCard';

const RighhtAlign = () => {
  const [RightTab, setRightTab] = useState('1');

  return (
    <Col sm='12' xl='6' className=' xl-100'>
      <Card>
        <HeaderCard title={TabsRightAlign} />
        <CardBody>
          <Nav className='nav nav-tabs nav-right'>
            <NavItem>
              <NavLink href='#javascript' className={RightTab === '1' ? 'active' : ''} onClick={() => setRightTab('1')}>
                <i className='icofont icofont-ui-home'></i>
                {Hometxt}
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink href='#javascript' className={RightTab === '2' ? 'active' : ''} onClick={() => setRightTab('2')}>
                <i className='icofont icofont-man-in-glasses'></i>
                {Profile}
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink href='#javascript' className={RightTab === '3' ? 'active' : ''} onClick={() => setRightTab('3')}>
                <i className='icofont icofont-contacts'></i>
                {Contact}
              </NavLink>
            </NavItem>
          </Nav>
          <TabContent activeTab={RightTab}>
            <TabPane className='fade show' tabId='1'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>
                {
                  'Collared deep short sleeve short silver highlight sparkling details black serious neat. Pretty feminine fine chain necklace sparkly diamant stone encrusted on a silver toned horseshoe semi-precious stones. Iconic style heritage brand outerwear collection lightweight showerproof material full zip fastening adjustable sleeves. Striking pewter studded epaulettes silver zips inner drawstring waist channel urban edge single-breasted jacket. Playful sleepsuit colourful poppers at the neckline and legs easy dressing contrast cuffs to the arms and ankles.'
                }
              </P>
            </TabPane>
            <TabPane tabId='2'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>
                {
                  'Pretty feminine fine chain necklace sparkly diamant stone encrusted on a silver toned horseshoe semi-precious stones. Iconic style heritage brand outerwear collection lightweight showerproof material full zip fastening adjustable sleeves. Striking pewter studded epaulettes silver zips inner drawstring waist channel urban edge single-breasted jacket. Playful sleepsuit colourful poppers at the neckline and legs easy dressing contrast cuffs to the arms and ankles.'
                }
              </P>
            </TabPane>
            <TabPane tabId='3'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>{' Regular fit viscose elastane leather black wool extra long linen blend parallel straight navy. Bow detail metallic eyelets leather lining luxurious finish classic courts formal slingback square toe contrasting cap.'}</P>
            </TabPane>
          </TabContent>
        </CardBody>
      </Card>
    </Col>
  );
};

export default RighhtAlign;
