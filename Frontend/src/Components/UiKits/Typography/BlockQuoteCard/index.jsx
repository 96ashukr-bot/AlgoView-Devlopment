import React from 'react';
import { Card, CardBody, CardHeader, Col } from 'reactstrap';
import { BlockQuotes, Footer, H5, P } from '../../../../AbstractElements';
import { Blockquotes, SourceTitle } from '../../../../Constant';

const BlockQuoteCard = () => {
  return (
    <Col sm="12">
      <Card>
        <CardHeader>
          <H5>{Blockquotes}</H5><span>{'Add a'} <code>&lt;{'footer className=\'blockquote-footer\''}&gt;</code> {'for identifying the source. Wrap the name of the source work in'} <code>&lt;{'cite'}&gt;</code>.</span>
        </CardHeader>
        <CardBody>
          <P attrPara={{ className: 'sub-title' }}>{'Naming a source'}</P>
          <BlockQuotes attrBlockQuote={{ className: 'blockquote mb-0' }}>
            <P attrPara={{ className: 'mb-0' }}>{'Lorem ipsum dolor sit amet'}{', consectetur adipiscing elit. Integer posuere erat a ante.'}</P>
          </BlockQuotes>
          <Footer attrFooter={{ className: 'blockquote-footer text-start mt-0' }}>{'Someone famous in'}
              <cite title="Source Title">{SourceTitle}</cite>
          </Footer>
          <P attrPara={{ className: 'sub-title' }} >{'Alignment Center'}</P>
          <BlockQuotes attrBlockQuote={{ className: 'blockquote text-center mb-0' }} >
            <P attrPara={{ className: 'mb-0' }} >{'Lorem ipsum dolor sit amet'}{', consectetur adipiscing elit. Integer posuere erat a ante.'}</P>
          </BlockQuotes>
          <Footer attrFooter={{ className: 'blockquote-footer text-center mt-0' }}>{'Someone famous in'}
              <cite title="Source Title">{SourceTitle}</cite>
          </Footer>
          <P attrPara={{ className: 'sub-title' }}>{'Alignment Right'}</P>
          <BlockQuotes attrBlockQuote={{ className: 'blockquote text-end mb-0' }} >
            <P attrPara={{ className: 'mb-0' }}>{'Lorem ipsum dolor sit amet'}{', consectetur adipiscing elit. Integer posuere erat a ante.'}</P>
          </BlockQuotes>
          <Footer attrFooter={{ className: 'blockquote-footer text-end m-0' }}>{'Someone famous in'}
              <cite title="Source Title">{SourceTitle}</cite>
          </Footer>
        </CardBody>
      </Card>
    </Col>
  );
};

export default BlockQuoteCard;