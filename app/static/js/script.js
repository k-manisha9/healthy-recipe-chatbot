// ✅ Set user_id in localStorage early
if (!localStorage.getItem("user_id")) {
    const newUserId = `user_${Date.now()}`;
    localStorage.setItem("user_id", newUserId);
}


document.getElementById('chat-window').addEventListener('click', function (event) {
    if (event.target.classList.contains('get-details-btn')) {
        const recipeName = event.target.getAttribute('data-recipe-name');

        const chatWindow = document.getElementById('chat-window');
        const userMessage = document.createElement('div');
        userMessage.classList.add('user-message');
        userMessage.innerHTML = `<strong>${recipeName}</strong> <br> Get Details`;

        chatWindow.appendChild(userMessage);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});



let pendingIncludeOnly = null;

// window.onload = function () {
//     document.getElementById('send-btn').addEventListener('click', async () => {
//         const input = document.getElementById('user-input').value.trim();
        
//         const sendButton = document.getElementById('send-btn');
//         document.getElementById('user-input').value = '';
//         if (!input) {
//             // alert("Please enter some ingredients!");
//             return;
//         }
//         const chatWindow = document.getElementById('chat-window');
//         let requestBody = { message: input };

//         try {
//             const response = await fetch('/chat', {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify(requestBody)
//             });

//             const data = await response.json();
        
//             // If this is the first message in a new chat, update the title
//             // const chatWindow = document.getElementById('chat-window');
//             if (chatWindow.children.length <= 1 && data.chat_title) {
//                 const activeChatItem = document.querySelector('.chat-item.active');
//                 if (activeChatItem) {
//                     const titleSpan = activeChatItem.querySelector('.chat-title');
//                     if (titleSpan) {
//                         titleSpan.textContent = data.chat_title;
                        
//                         // Update localStorage
//                         const savedChats = JSON.parse(localStorage.getItem('chatSessions')) || [];
//                         const chatId = activeChatItem.dataset.chatId;
//                         const chatIndex = savedChats.findIndex(c => c.id === chatId);
//                         if (chatIndex !== -1) {
//                             savedChats[chatIndex].title = data.chat_title;
//                             localStorage.setItem('chatSessions', JSON.stringify(savedChats));
//                         }
//                     }
//                 }
//             }
//             chatWindow.innerHTML += `<div class='chat-message user-message'>${input}</div>`;
//             saveChatHistory();
//             sendButton.disabled = true;
//             // If the user replied 'yes' and we had pending include-only ingredients
//             if (pendingIncludeOnly && ["yes", "yeah", "sure", "ok"].includes(input.toLowerCase())) {
//                 requestBody = {
//                     message: `I have ${pendingIncludeOnly.join(", ")}`
//                 };
//                 pendingIncludeOnly = null;
//             }
//             if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

//             console.log("Response from /chat:", data);
//             // console.log("Recipes received from backend:", data.recipes);

//             // data.recipes.forEach(recipe => {
//             //     console.log("Recipe ID:", recipe.id, "Title:", recipe.title);
//             // });

//             // console.log("Image URL:", data.recipes[0].id);
//             if (data.recipes && data.recipes.length > 0) {
//                 chatWindow.innerHTML+=`<div class='chat-message bot-message recipe-card'>${data.friendly_intro}</div>`
//                 data.recipes.forEach(recipe => {
//                     if (recipe.id) {
//                         console.log("hiiiiiiiiiiii...........")
//                         // console.log("hii....    ",recipe.image)
//                         const recipeDiv = `
//                             <div class='chat-message bot-message recipe-card'>
//                                 <strong>${recipe.title}</strong><br>
//                                 <img src="${recipe.image}" alt="${recipe.title}" width="200px"><br>
//                                 <div class="recipe-cost">
//                                     <strong>Number of missed ingredients:</strong> ${recipe.missedIngredientCount}<br>
//                                     <strong>Number of used ingredients:</strong> ${recipe.usedIngredientCount}
//                                 </div>
//                                 <button class="get-details-btn" data-recipe-name="${recipe.title}" onclick="getRecipeDetails(${recipe.id})">Get Details</button>
//                             </div>
//                         `;
//                         chatWindow.innerHTML += recipeDiv;
//                     }
//                     else {
//                         console.warn("Skipping recipe with missing ID:", recipe);
//                     }
//                 });
//             }
//             else if (data.text) {
//                 chatWindow.innerHTML += `<div class='chat-message bot-message'>${data.text}</div>`;
//                 if (data.followup && data.include_only) {
//                     pendingIncludeOnly = data.include_only;
//                 }
//             }
//             // else if(data) {
//             //     chatWindow.innerHTML += `<div class='chat-message bot-message'>${data}</div>`;
//             // }
//             console.log("Image URL:", data.fallback_recipes[0].image);
//             if (data.fallback_recipes && data.fallback_recipes.length > 0) {
//                 const fallbackdiv = `
//                                     <div class='chat-message bot-message recipe-card'>
//                                     <strong>According to your health conditions, there are no safe recipes matching the given ingredients. You can try these recipes out since its safe and healthy according to your health conditions.</strong>
//                                     </div>
//                                     `;
//                 chatWindow.innerHTML += fallbackdiv;
//                 data.fallback_recipes.forEach(recipe => {
//                     if (recipe.id) {
//                         const recipeDiv = `
//                             <div class='chat-message bot-message recipe-card'>
//                                 <strong>${recipe.title}</strong><br>
//                                 <img src="${recipe.image}" alt="${recipe.title}" width="200px"><br>
                                
//                                 <button class="get-details-btn" data-recipe-name="${recipe.title}" onclick="getRecipeDetails(${recipe.id})">Get Details</button>
//                             </div>
//                         `;
//                         chatWindow.innerHTML += recipeDiv;
//                     }
//                     else {
//                         console.warn("Skipping recipe with missing ID:", recipe);
//                     }
//                 });
//             }
//             else {
//                 const fallbackdiv = `
//                                     <div class='chat-message bot-message recipe-card'>
//                                     <strong>Could not find recipes with the given ingredients and given health conditions</strong>
//                                     </div>
//                                     `;
//                 chatWindow.innerHTML += fallbackdiv;
//             }
//             saveChatHistory();
//         }
//         catch (error) {
//             // ... error handling ...
//             console.error("Error fetching recipes.....:", error);
//         }
//         finally {
//             sendButton.disabled = false;
//         }
//     });
// };



document.getElementById('send-btn').addEventListener('click', async function () {
    const input = document.getElementById('user-input');
    const userText = input.value.trim();
    if (!userText) return;

    appendMessage('user', userText,Date.now().toString());
    input.value = '';

    if (isCollectingDietInfo && currentChatStep < chatSteps.length) {
        handleDietPlanInput(userText);
    } else {
        await sendToChatRoute(userText);
    }
});

function handleDietPlanInput(userText) {
    const step = chatSteps[currentChatStep];
    const isValid = step.validate ? step.validate(userText) : true;

    if (!isValid) {
        appendMessage('chatbot', `Please enter a valid ${step.key}.`);
        return;
    }

    userInputs[step.key] = userText;
    currentChatStep++;

    // Ask next question or submit data
    if (currentChatStep < chatSteps.length) {
        setTimeout(askNextQuestion, 500);
    } else {
        appendMessage('chatbot', 'Thanks! Preparing your personalized diet plan...');
        isCollectingDietInfo = false;

        fetch('/get_diet_plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                age: parseInt(userInputs.age),
                gender: userInputs.gender,
                height: parseInt(userInputs.height),
                weight: parseInt(userInputs.weight),
                activity: userInputs.activity,
                diet: userInputs.diet,
                disease: userInputs.disease
            })
        })
        .then(res => res.json())
        .then(data => {
            displayMacronutrients(data.macros);
            displayWeeklyPlan(data.weekly_plan);
        })
        .catch(err => {
            console.error('Error fetching diet plan:', err);
            appendMessage('chatbot', '❌ Failed to generate diet plan. Please try again later.');
        });
    }
}


async function sendToChatRoute(userText) {
    const chatWindow = document.getElementById('chat-window');
    const sendButton = document.getElementById('send-btn');
    let requestBody = { message: userText };

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        // Chat title logic for new chats
        if (chatWindow.children.length <= 1 && data.chat_title) {
            const activeChatItem = document.querySelector('.chat-item.active');
            if (activeChatItem) {
                const titleSpan = activeChatItem.querySelector('.chat-title');
                if (titleSpan) {
                    titleSpan.textContent = data.chat_title;
                    const savedChats = JSON.parse(localStorage.getItem('chatSessions')) || [];
                    const chatId = activeChatItem.dataset.chatId;
                    const chatIndex = savedChats.findIndex(c => c.id === chatId);
                    if (chatIndex !== -1) {
                        savedChats[chatIndex].title = data.chat_title;
                        localStorage.setItem('chatSessions', JSON.stringify(savedChats));
                    }
                }
            }
        }

        // Show intro message
        if (data.friendly_intro) {
            chatWindow.innerHTML += `<div class='chat-message bot-message recipe-card'>${data.friendly_intro}</div>`;
        }
        console.log("data::::::::::",data)
        // Show recipes from local dataset
        if (data.source == "local_dataset") {
            if (data.recipes && data.recipes.length > 0) {
                data.recipes.forEach(recipe => {
                    if (recipe) {
                        const recipeDiv = `
                            <div class='chat-message bot-message recipe-card'>
                                <strong>${recipe.title}</strong><br>
                                <h3>Instructions:</h3>
                                <div>${recipe.instructions}</div>
                                <div class="recipe-cost">
                                    <strong>Preparation Time:</strong> ${recipe.prep_time}<br>
                                    <strong>Cook Time:</strong> ${recipe.cook_time}<br>
                                    <strong>Total Time:</strong> ${recipe.total_time}<br>
                                    <strong>Servings:</strong> ${recipe.servings}<br>
                                    <strong>Diet Type:</strong> ${recipe.diet}
                                </div>
                            </div>`;
                        chatWindow.innerHTML += recipeDiv;
                    }
                });
            }
        }
        // Show recipes from spoonacular
        else if (data.recipes && data.recipes.length > 0) {
            data.recipes.forEach(recipe => {
                if (recipe.id) {
                    const recipeDiv = `
                        <div class='chat-message bot-message recipe-card'>
                            <strong>${recipe.title}</strong><br>
                            <img src="${recipe.image}" alt="${recipe.title}" width="200px"><br>
                            <div class="recipe-cost">
                                <strong>Number of missed ingredients:</strong> ${recipe.missedIngredientCount}<br>
                                <strong>Number of used ingredients:</strong> ${recipe.usedIngredientCount}
                            </div>
                            <button class="get-details-btn" data-recipe-name="${recipe.title}" onclick="getRecipeDetails(${recipe.id})">Get Details</button>
                        </div>`;
                    chatWindow.innerHTML += recipeDiv;
                }
            });
        } else if (data.text) {
            chatWindow.innerHTML += `<div class='chat-message bot-message'>${data.text}</div>`;
            if (data.followup && data.include_only) {
                pendingIncludeOnly = data.include_only;
            }
        }

        // Show fallback recipes if needed
        if (data.fallback_recipes && data.fallback_recipes.length > 0) {
            chatWindow.innerHTML += `<div class='chat-message bot-message recipe-card'>
                <strong>These are some recipe suggestions according to your health conditions:</strong></div>`;
            data.fallback_recipes.forEach(recipe => {
                if (recipe.id) {
                    const fallbackDiv = `
                        <div class='chat-message bot-message recipe-card'>
                            <strong>${recipe.title}</strong><br>
                            <img src="${recipe.image}" alt="${recipe.title}" width="200px"><br>
                            <button class="get-details-btn" data-recipe-name="${recipe.title}" onclick="getRecipeDetails(${recipe.id})">Get Details</button>
                        </div>`;
                    chatWindow.innerHTML += fallbackDiv;
                }
            });
        }

        saveChatHistory();
        chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch (error) {
        console.error("Error sending message to /chat:", error);
        appendMessage('chatbot', '❌ Failed to fetch recipe suggestions.');
    } finally {
        sendButton.disabled = false;
    }
}




async function getRecipeDetails(recipeId) {
    try {
        const response = await fetch(`/getdetail?recipe_id=${recipeId}`);
        if (!response.ok) throw new Error('Failed to fetch recipe details');
        
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        console.log("data result-->>",data)
        // Build ingredients list
        const ingredientsList = data.ingredients.map(ing => 
            `• ${ing.amount} ${ing.unit} ${ing.name}`
        ).join('<br>');

        // Cost display
        const costDisplay = data.hasCostData 
            ? `<div class="cost-display">
                  <p><strong>Total Cost:</strong> ₹${data.totalCost.toFixed(2)}</p>
                  <p><strong>Per Serving:</strong> ₹${data.costPerServing.toFixed(2)}</p>
               </div>`
            : '<p class="no-cost">Cost information not available</p>';

        // Create full recipe display
        const recipeHTML = `
            <div class="chat-message bot-message">
                <h2>${data.title}</h2>
                <img src="${data.image}" alt="${data.title}" width="300">
                <p><strong>Ready in:</strong> ${data.readyInMinutes} minutes</p>
                <p><strong>Servings:</strong> ${data.servings}</p>
                <h3>Ingredients</h3>
                ${ingredientsList}
                ${costDisplay}
                <h3>Instructions</h3>
                <p>${data.instructions}</p>
            </div>
        `;

        document.getElementById('chat-window').innerHTML += recipeHTML;
    } catch (error) {
        console.error("Error:", error);
        alert("Error loading recipe: " + error.message);
    }
}



if (!localStorage.getItem('chatSessions')) {
    localStorage.setItem('chatSessions', JSON.stringify([]));
}

// Replace the entire DOMContentLoaded event listener with this:
document.addEventListener('DOMContentLoaded', () => {
    const savedChatsList = document.getElementById('saved-chats');
    const chatWindow = document.getElementById('chat-window');
    
    // Load any existing chats from localStorage
    const savedChats = JSON.parse(localStorage.getItem('chatSessions')) || [];
    
    // Render saved chats in sidebar
    savedChats.forEach((chat, index) => {
        const li = document.createElement('li');
        li.textContent = chat.title || `Chat ${index + 1}`;
        li.className = 'chat-title';
        li.dataset.sessionId = chat.id;
        
        li.addEventListener('click', () => {
            // Load the selected chat
            loadChat(chat.id);
            
            // Highlight active chat
            document.querySelectorAll('.chat-title').forEach(item => {
                item.classList.remove('active');
            });
            li.classList.add('active');
        });
        
        savedChatsList.appendChild(li);
    });
    
    // If we have saved chats, load the first one
    // if (savedChats.length > 0) {
    //     loadChat(savedChats[0].id);
    //     savedChatsList.children[0].classList.add('active');
    // }
});



function loadChat(chatId) {
    try {
        const chatWindow = document.getElementById('chat-window');
        const savedChats = JSON.parse(localStorage.getItem('chatSessions')) || [];
        const chat = savedChats.find(c => c.id === chatId);
        
        if (chat) {
            chatWindow.innerHTML = chat.content || '';
            chatWindow.scrollTop = chatWindow.scrollHeight;
        } else {
            console.warn(`Chat with ID ${chatId} not found`);
            chatWindow.innerHTML = '<div class="no-chat">Select a chat or start a new one</div>';
        }
    } catch (error) {
        console.error('Error loading chat:', error);
        document.getElementById('chat-window').innerHTML = 
            '<div class="error-message">Error loading chat content</div>';
    }
}

// Update the saveChatHistory function
function saveChatHistory() {
    const activeChatItem = document.querySelector('.chat-item.active');
    if (!activeChatItem) return;
    
    const chatId = activeChatItem.dataset.chatId;
    const chatWindow = document.getElementById('chat-window');
    
    try {
        const savedChats = JSON.parse(localStorage.getItem('chatSessions')) || [];
        const chatIndex = savedChats.findIndex(c => c.id === chatId);
        
        if (chatIndex !== -1) {
            savedChats[chatIndex].content = chatWindow.innerHTML;
            localStorage.setItem('chatSessions', JSON.stringify(savedChats));
        }
    } catch (error) {
        console.error('Error saving chat history:', error);
    }
}


// Function to render all chat items in sidebar
function renderChatList() {
    const savedChatsList = document.getElementById('saved-chats');
    savedChatsList.innerHTML = ''; // Completely clear the list first
    
    try {
        const savedChats = JSON.parse(localStorage.getItem('chatSessions') || '[]');
        
        // Sort chats by creation date (newest first)
        savedChats.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        
        savedChats.forEach(chat => {
            const li = document.createElement('li');
            li.className = 'chat-item';
            li.dataset.chatId = chat.id;
            
            // Chat title
            const titleSpan = document.createElement('span');
            titleSpan.className = 'chat-title';
            titleSpan.textContent = chat.title;
            
            // Delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-chat-btn';
            deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteChat(chat.id);
            });
            
            // Click handler for the entire item
            // Inside renderChatList(), update the li.addEventListener code:
            li.addEventListener('click', (e) => {
                // Don't trigger if clicking on delete button
                if (!e.target.classList.contains('delete-chat-btn')) {
                    loadChat(chat.id);
                    document.querySelectorAll('.chat-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    li.classList.add('active');
                }
            });
            
            li.appendChild(titleSpan);
            li.appendChild(deleteBtn);
            savedChatsList.appendChild(li);
        });
    } catch (error) {
        console.error('Error rendering chat list:', error);
    }
}

function deleteChat(chatId) {
    if (confirm('Are you sure you want to delete this chat?')) {
        try {
            // Get current chats from localStorage
            let savedChats = JSON.parse(localStorage.getItem('chatSessions') || '[]');
            
            // Filter out the deleted chat
            savedChats = savedChats.filter(chat => chat.id !== chatId);
            
            // Update localStorage
            localStorage.setItem('chatSessions', JSON.stringify(savedChats));
            
            // Re-render the chat list
            renderChatList();
            
            // Clear chat window if deleted chat was active
            const activeChat = document.querySelector('.chat-item.active');
            if (activeChat && activeChat.dataset.chatId === chatId) {
                document.getElementById('chat-window').innerHTML = '';
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
            alert('Failed to delete chat. Please try again.');
        }
    }
}

// Update your DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    // Initialize if empty
    if (!localStorage.getItem('chatSessions')) {
        localStorage.setItem('chatSessions', JSON.stringify([]));
    }
    
    renderChatList();
    
    // Debug: Log current chats
    console.log('Current chats:', JSON.parse(localStorage.getItem('chatSessions')));
    
    // Load first chat if available
    const savedChats = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    if (savedChats.length > 0) {
        loadChat(savedChats[0].id);
        const firstChatItem = document.querySelector('.chat-item');
        if (firstChatItem) {
            firstChatItem.classList.add('active');
        }
    }
    setInterval(saveChatHistory, 5000);
});

// Update your new chat button event listener
document.getElementById('new-chat-btn').addEventListener('click', function() {
    try {
        const savedChats = JSON.parse(localStorage.getItem('chatSessions') || '[]');
        
        // Generate a unique ID
        const newChatId = Date.now().toString();
        
        // Create new chat with unique title
        let chatNumber = savedChats.length + 1;
        let chatTitle = `Chat ${chatNumber}`;
        
        // Ensure title is unique
        while (savedChats.some(chat => chat.title === chatTitle)) {
            chatNumber++;
            chatTitle = `Chat ${chatNumber}`;
        }
        
        const newChat = {
            id: newChatId,
            title: 'New Recipe Search',
            // title: chatTitle,
            content: '',
            createdAt: new Date().toISOString()
        };
        
        // Add to beginning of array (newest first)
        savedChats.unshift(newChat);
        localStorage.setItem('chatSessions', JSON.stringify(savedChats));
        
        // Refresh UI
        renderChatList();
        loadChat(newChatId);
        
        // Set as active
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.chatId === newChatId) {
                item.classList.add('active');
            }
        });
    } catch (error) {
        console.error('Error creating new chat:', error);
    }
});



// Global state for diet plan conversation
let currentChatStep = 0;
let userInputs = {};
let isCollectingDietInfo = false;

const chatSteps = [
    { key: 'age', question: "What's your age?" },
    { key: 'gender', question: "What's your gender?" },
    { key: 'height', question: "What's your height in cm?" },
    { key: 'weight', question: "What's your weight in kg?" },
    { key: 'activity', question: "What is your daily activity level? (e.g., very active, moderately active, sedentary, lightly active, extra active)" },
    { key: 'disease', question: "Do you have any disease? If yes then please write it down." },
    { key: 'diet', question: "Do you have any dietary preference? If yes then please write it down (e.g., vegan, omnivore, vegetarian)" },
];

// Diet Plan Button Logic
document.getElementById('get-diet-plan').addEventListener('click', function () {
    try {
        const savedChats = JSON.parse(localStorage.getItem('chatSessions') || '[]');
        currentChatId = Date.now().toString();

        const chatTitle = `Diet Plan`;

        const newChat = {
            id: currentChatId,
            title: chatTitle,
            messages: [],
            createdAt: new Date().toISOString()
        };

        savedChats.unshift(newChat);
        localStorage.setItem('chatSessions', JSON.stringify(savedChats));

        renderChatList();
        loadChat(currentChatId);

        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.chatId === currentChatId) {
                item.classList.add('active');
            }
        });

        startDietPlanConversation();

    } catch (error) {
        console.error('Error creating new chat:', error);
    }
});

function startDietPlanConversation() {
    currentChatStep = 0;
    userInputs = {};
    isCollectingDietInfo = true;
    document.getElementById('chat-window').innerHTML = '';
    askNextQuestion();
}


function askNextQuestion() {
    if (currentChatStep < chatSteps.length) {
        const question = chatSteps[currentChatStep].question;
        appendMessage('chatbot', question);
    } else {
        

        // Call backend with collected user inputs
        fetch('/get_diet_plan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                age: parseInt(userInputs.age),
                gender: userInputs.gender,
                height: parseInt(userInputs.height),
                weight: parseInt(userInputs.weight),
                activity: userInputs.activity,
                diet: userInputs.diet,
                disease: userInputs.disease
            })
        })
        .then(res => res.json())
        .then(data => {
            displayMacronutrients(data.macros);
            displayWeeklyPlan(data.weekly_plan);
        })
        .catch(err => {
            console.error('Error fetching diet plan:', err);
            appendMessage('chatbot', '❌ Failed to generate diet plan. Please try again later.');
        });
        appendMessage('chatbot', 'Thanks! Preparing your personalized diet plan...');
        isCollectingDietInfo = false;
    }
}


// document.getElementById('send-btn').addEventListener('click', function () {
//     const input = document.getElementById('user-input');
//     const userText = input.value.trim();
//     if (!userText) return;

//     appendMessage('user', userText);
//     input.value = '';

//     if (isCollectingDietInfo && currentChatStep < chatSteps.length) {
//         const step = chatSteps[currentChatStep];
//         const isValid = step.validate ? step.validate(userText) : true;

//         if (!isValid) {
//             appendMessage('chatbot', `Please enter a valid ${step.key} (numeric value).`);
//             return;
//         }

//         userInputs[step.key] = userText;
//         currentChatStep++;
//         setTimeout(askNextQuestion, 500);
//     } else {
//         // Optional: Handle general queries here
//         appendMessage('chatbot', "You said: " + userText);
//     }
// });



// Append chat message and save


function appendMessage(sender, text,currentChatId) {
    const chatWindow = document.getElementById('chat-window');
    const msgDiv = document.createElement('div');
    msgDiv.className = sender === 'chatbot' ? 'chat-message bot-message' : 'user-message';
    msgDiv.innerText = text;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    saveMessageToChat(currentChatId, sender, text);
}

// Save message to localStorage under current chat
function saveMessageToChat(chatId, sender, text) {
    if (!chatId) return;
    const chats = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    const chatIndex = chats.findIndex(c => c.id === chatId);
    if (chatIndex !== -1) {
        chats[chatIndex].messages.push({ sender, text, time: new Date().toISOString() });
        localStorage.setItem('chatSessions', JSON.stringify(chats));
    }
}

// Validate numeric inputs
function isNumber(value) {
    return !isNaN(value) && Number(value) > 0;
}

function displayMacronutrients(macros) {
    const chatWindow = document.getElementById('chat-window');
    const div = document.createElement("div");
    div.className = 'diet-card';
    div.innerHTML = `
      <h3>Daily Macronutrient Needs</h3>
      <p class="meal-row"><strong>Calories:</strong> ${macros.Calories} kcal</p>
      <p class="meal-row"><strong>Protein:</strong> ${macros.Protein} g</p>
      <p class="meal-row"><strong>Carbohydrates:</strong> ${macros.Carbohydrates} g</p>
    `;
    chatWindow.appendChild(div);
  }
  

function displayWeeklyPlan(weeklyPlan) {
    const chatWindow = document.getElementById('chat-window');

    weeklyPlan.forEach(day => {
        const card = document.createElement('div');
        card.className = 'diet-card';

        card.innerHTML = `
            <h3>${day.Day}</h3>
            <div class="meal-row"><strong>🍳 Breakfast:</strong> ${day.Breakfast} (${day.Breakfast_Calories} kcal)</div>
            <div class="meal-row"><strong>🥗 Lunch:</strong> ${day.Lunch} (${day.Lunch_Calories} kcal)</div>
            <div class="meal-row"><strong>🍽 Dinner:</strong> ${day.Dinner} (${day.Dinner_Calories} kcal)</div>
            <div class="meal-row"><strong>🍎 Snack:</strong> ${day.Snack} (${day.Snack_Calories} kcal)</div>
            <div class="macro-summary">Total: ${day["Total Calories"]} kcal | ${day["Total Protein"]} g protein | ${day["Total Carbohydrates"]} g carbs</div>
        `;

        chatWindow.appendChild(card);
    });

    chatWindow.scrollTop = chatWindow.scrollHeight;
}
