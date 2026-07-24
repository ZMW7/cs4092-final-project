
def getUserType():
    print("Welcome to the marketplace! Signing in as customer (y/n)")
    answer = input()
    match answer:
        case 'n' | 'N':
            print("Press 's' for seller sign-in, 'm' for moderator sign-in, or any other symbol to go back")
            nextAnswer = input()
            match nextAnswer:
                case 's':
                    pass
                case 'm':
                    pass
                case _:
                    getUserType()
        case _:
            pass

def main():
    return;

if __name__ == '__main__':
    main();