export const Javadata = `
    /* Sample JavaScript edit source */
    // Define a module
    var app = angular.module('app', ['ui.bootstrap']);
    // Define a conroller.
    app.controller('GrokController', ['$scope', '$filter',
        function($scope, $filter) {
            $scope.today = function() {
                $scope.dt = new Date();
            };
            $scope.today();
            $scope.isOpened = false;
            $scope.open = function($event) {
                $event.preventDefault();
                $event.stopPropagation();
                $scope.isOpened = true;
            };
    }]);
    /* End of sample edit source */
                    `;

export const HtmlData = `
    <!--Page header start-->
    <div class="page-header">
        <Row>
            <Col xl="6">
                <H3>Ace Text editor</H3>
                <small>Cuba Admin panel</small>
            </Col>
            <Col xl="6">
                <OL class="breadcrumb pull-right">
                    <LI class="breadcrumb-item"></LI>
                    <LI class="breadcrumb-item">Editor </LI>
                    <LI class="breadcrumb-item active">Ace Text editor</LI>
                </OL>
            </Col>
        <Row>
    </div>
    <!--Page header end-->
`;

export const CssData = `
    .text-layer{
        font: 12px Monaco, "Courier New", monospace;
        font-size: 3vmin;
        cursor: text;
    }

    .blinker {
        animation: blink 1s linear infinite alternate;
    }

    @keyframes blink {
        0%, 40% {
          opacity: 1
        }
        40.5%, 100% {
          opacity: 1
        }
    }
             
    img[title]:before{
        content: attr(title) 
        white-space: pre;
        display: block;
        background: url(asdasd); 
    }
            
    @viewport {
        min-zoom: 1;
        max-zoom: 200%;
        user-zoom: fixed;
    }
`;

export const Typescript = `
    class Animal{  
            String color="white";  
    }  

    class Dog extends Animal{  
        String color="black";  
        void printColor(){  
            System.out.println(color);//prints color of Dog class  
            System.out.println(super.color);
        }    
    }  

    class TestSuper1{  
        public static void main(String args[]){  
            Dog d=new Dog();  
            d.printColor();  
        }
    }  
`;
