import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { H4, H5, P } from '../../../AbstractElements';
import Alerts from '../../../CommonElements/Alert';
import { AdditionalContent } from '../../../Constant';

const AdditionalContents = () => {

  return (
    <Col sm="12">
      <Card>
        <CardHeader>
          <H5>{AdditionalContent}</H5><span>{'Alerts can also contain additional HTML elements like headings, paragraphs and dividers.'}</span>
        </CardHeader>
        <CardBody>
          <Alerts attrAlert={{ color: 'primary ' }} >
            <H4 attrH4={{ className: 'alert-heading' }} >{'Well done!'}</H4>
            <P>{'Aww yeah, you successfully read this important alert message. This example text is going to run a bit longer so that you can see how spacing within an alert works with this kind of content.'}</P>
            <hr />
            <P attrPara={{ className: 'mb-0' }}>{'Whenever you need to, be sure to use margin utilities to keep things nice and tidy.'}</P>
          </Alerts>
          <Alerts attrAlert={{ color: 'secondary' }} >
            <H4 attrH4={{ className: 'alert-heading' }}>{'Well done!'}</H4>
            <P>{'Aww yeah, you successfully read this important alert message. This example text is going to run a bit longer so that you can see how spacing within an alert works with this kind of content.'}</P>
            <hr />
            <P attrPara={{ className: 'mb-0' }}>{'Whenever you need to, be sure to use margin utilities to keep things nice and tidy.'}</P>
          </Alerts>
          <Alerts attrAlert={{ color: 'success' }} >
            <H4 attrH4={{ className: 'alert-heading' }}>{'Well done!'}</H4>
            <P>{'Aww yeah, you successfully read this important alert message. This example text is going to run a bit longer so that you can see how spacing within an alert works with this kind of content.'}</P>
            <hr />
            <P attrPara={{ className: 'mb-0' }} >{'Whenever you need to, be sure to use margin utilities to keep things nice and tidy.'}</P>
          </Alerts>
          <Alerts attrAlert={{ color: 'danger' }} >
            <H4 attrH4={{ className: 'alert-heading' }}>{'Well done!'}</H4>
            <P>{'Aww yeah, you successfully read this important alert message. This example text is going to run a bit longer so that you can see how spacing within an alert works with this kind of content.'}</P>
            <hr />
            <P attrPara={{ className: 'mb-0' }} >{'Whenever you need to, be sure to use margin utilities to keep things nice and tidy.'}</P>
          </Alerts>
          <Alerts attrAlert={{ color: 'info' }} >
            <H4 attrH4={{ className: 'alert-heading' }}>{'Well done!'}</H4>
            <P>{'Aww yeah, you successfully read this important alert message. This example text is going to run a bit longer so that you can see how spacing within an alert works with this kind of content.'}</P>
            <hr />
            <P attrPara={{ className: 'mb-0' }} >{'Whenever you need to, be sure to use margin utilities to keep things nice and tidy.'}</P>
          </Alerts>
          <Alerts attrAlert={{ color: 'light' }} >
            <H4 attrH4 className="alert-heading">{'Well done!'}</H4>
            <P>{'Aww yeah, you successfully read this important alert message. This example text is going to run a bit longer so that you can see how spacing within an alert works with this kind of content.'}</P>
            <hr />
            <P attrPara={{ className: 'mb-0' }} >{'Whenever you need to, be sure to use margin utilities to keep things nice and tidy.'}</P>
          </Alerts>
          <Alerts attrAlert={{ color: 'dark' }} >
            <H4 attrH4={{ className: 'alert-heading' }} >{'Well done!'}</H4>
            <P>{'Aww yeah, you successfully read this important alert message. This example text is going to run a bit longer so that you can see how spacing within an alert works with this kind of content.'}</P>
            <hr />
            <P attrPara={{ className: 'mb-0' }} >{'Whenever you need to, be sure to use margin utilities to keep things nice and tidy.'}</P>
          </Alerts>
        </CardBody>
      </Card>
    </Col>
  );
};

export default AdditionalContents;