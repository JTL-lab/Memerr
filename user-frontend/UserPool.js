import { CognitoUserPool } from "amazon-cognito-identity-js";

const poolData = {
    UserPoolId: "us-east-1_2xLbaGSV5",
    ClientId: "66oaupmsid03n7ugdbseid111s"
}

export default new CognitoUserPool(poolData);