

def sum_of_integers(number:int) -> int:
    
    result = 0
    while number >0:
        digit=number%10
        number //=10
        result +=digit
    return result


def is_polindrome(word:str) -> bool:
    length=len(word)
    first_half=[]
    end_half=[]
    if length % 2 == 1:
        middle=int(((length + 1) / 2)-1)
        for i in range(middle):
            first_half.append(word[i])
        for y in range(middle+1,len(word)):
            end_half.append(word[y])
        return first_half==end_half[::-1]
    else :
        for i in range(int(length/2)):
            first_half.append(word[i])
        for y in range(int(length/2),int(length)):
            end_half.append(word[y])
    return first_half==end_half[::-1]
  

numbers = [12, 45, 7, 89, 34, 89, 23]


for i in numbers:
    while len(numbers) > 2 :
        


    





  

    

        







